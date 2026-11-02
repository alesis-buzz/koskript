const { createConnection, TextDocuments, TextDocumentSyncKind, CompletionItemKind } = require("vscode-languageserver/node");
const { TextDocument } = require("vscode-languageserver-textdocument");
const { parse, collectSymbols, enclosingClass } = require("./parser");
const { fileURLToPath } = require("url");
const path = require("path");
const fs = require("fs");

const connection = createConnection(process.stdin, process.stdout);
const documents = new TextDocuments(TextDocument);

const KEYWORDS = ["let","const","fun","wrapper","class","extends","namespace","error","import","as","if","elseif","else","while","for","foreach","return","break","continue","throw","try","catch","finally","static","public","private","constructor","this","super","new","true","false","null","and","or","not","in"];
const BUILTINS = ["print","len","type","typeof","str","int","float","bool","range","copy","loadcode","array","map","string","bytes","math","json"];

// Kept in sync with the Python standard library (src/koskript/stdlib).
const STDLIB_MEMBERS = {
  "array": ["push","pop","insert","remove_at","clear","sort","sort_by","reverse","slice","join","index_of","contains","map","filter","reduce","each"],
  "map": ["keys","values","has","remove","merge"],
  "string": ["upper","lower","trim","split","starts_with","ends_with","replace","find","contains","slice","repeat","pad_left","pad_right","chars"],
  "bytes": ["from_string","to_string","hex","from_hex","from_array","to_array","contains","slice"],
  "math": ["pi","e","abs","floor","ceil","round","sqrt","pow","min","max","clamp","random","random_int","log","exp","sin","cos","tan"],
  "json": ["encode","decode"],
};
const STDLIB_CONSTANTS = new Set(["pi", "e"]);

const SYMBOL_KINDS = {
  namespace: 3,
  class: 5,
  function: 12,
  error: 12,
  constant: 14,
  variable: 13,
};

function completionKind(kind) {
  switch (kind) {
    case "class": return CompletionItemKind.Class;
    case "constant": return CompletionItemKind.Constant;
    case "field": return CompletionItemKind.Field;
    case "method": return CompletionItemKind.Method;
    case "variable": return CompletionItemKind.Variable;
    default: return CompletionItemKind.Function;
  }
}

function pushUnique(list, value) {
  if (!list.includes(value)) list.push(value);
}

documents.onDidChangeContent(change => {
  validate(change.document);
});

documents.onDidOpen(event => {
  validate(event.document);
});

documents.onDidClose(event => {
  connection.sendDiagnostics({ uri: event.document.uri, diagnostics: [] });
});

function validate(doc) {
  const text = doc.getText();
  const diagnostics = [];
  try {
    parse(text, { allowBodyless: /\.kosh$/i.test(doc.uri) });
  } catch (e) {
    const line = Number.isInteger(e.line) ? e.line : 0;
    const character = Number.isInteger(e.character) ? e.character : 0;
    diagnostics.push({
      severity: 1,
      range: {
        start: { line, character },
        end: { line, character: character + 1 },
      },
      message: String(e.message || e),
      source: "koskript"
    });
  }
  connection.sendDiagnostics({ uri: doc.uri, diagnostics });
}

connection.onInitialize(() => {
  return {
    capabilities: {
      textDocumentSync: TextDocumentSyncKind.Incremental,
      completionProvider: { triggerCharacters: [".", ":"] },
      documentSymbolProvider: true
    }
  };
});

connection.onCompletion(params => {
  try {
    return complete(params);
  } catch (e) {
    connection.console.error(String(e && e.stack ? e.stack : e));
    return [];
  }
});

function complete(params) {
  const doc = documents.get(params.textDocument.uri);
  const text = doc ? doc.getText() : "";
  const bd = baseDir(params.textDocument.uri);
  const syms = collectSymbols(text, bd);
  addHeaderSymbols(syms, bd);

  const pos = params.position;
  const line = text.split("\n")[pos.line] || "";
  const before = line.slice(0, pos.character);
  const offset = doc ? doc.offsetAt(pos) : 0;

  const items = [];
  const seen = new Set();
  const add = (label, kind) => {
    if (!label || seen.has(label)) return;
    seen.add(label);
    items.push({ label, kind });
  };

  // Walk `extends` chains for class members.
  const getMembers = (cls, depth) => {
    depth = depth || 0;
    if (!cls || depth > 8 || !Array.isArray(syms.members[cls])) return [];
    let out = syms.members[cls].slice();
    const parent = syms.parents[cls];
    if (parent && syms.members[parent]) {
      for (const pm of getMembers(parent, depth + 1)) {
        if (!out.some(x => x.name === pm.name)) out.push(pm);
      }
    }
    return out;
  };

  const addMembers = (members, partial) => {
    for (const m of members) {
      if (partial && !m.name.startsWith(partial)) continue;
      add(m.name, completionKind(m.kind));
    }
  };

  // `receiver.` or `receiver::` (optionally with a typed prefix)
  const m = /([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)(::|\.)([A-Za-z0-9_]*)$/.exec(before);
  if (m) {
    const receiver = m[1];
    const partial = m[3];

    if (receiver === "this" || receiver === "super") {
      const cls = enclosingClass(text, offset);
      if (cls) {
        const target = receiver === "this" ? cls : (syms.parents[cls] || cls);
        addMembers(getMembers(target), partial);
        return items;
      }
    } else {
      const ns = resolveNamespace(syms, receiver);
      if (ns) {
        addMembers(ns.functions.map(name => ({ name, kind: "function" })), partial);
        addMembers(ns.classes.map(name => ({ name, kind: "class" })), partial);
        addMembers(ns.constants.map(name => ({ name, kind: "constant" })), partial);
        return items;
      }
      if (!receiver.includes(".") && STDLIB_MEMBERS[receiver]) {
        addMembers(STDLIB_MEMBERS[receiver].map(name => ({
          name,
          kind: STDLIB_CONSTANTS.has(name) ? "constant" : "function",
        })), partial);
        return items;
      }
      if (syms.instantiations[receiver]) {
        addMembers(getMembers(syms.instantiations[receiver]), partial);
        return items;
      }
      if (syms.members[receiver]) {
        addMembers(getMembers(receiver), partial);
        return items;
      }
    }
  }

  // `.` or `::` with no receiver, inside a class body.
  if (/(::|\.)$/.test(before)) {
    const cls = enclosingClass(text, offset);
    if (cls) {
      addMembers(getMembers(cls), "");
      return items;
    }
  }

  for (const kw of KEYWORDS) add(kw, CompletionItemKind.Keyword);
  for (const b of BUILTINS) add(b, CompletionItemKind.Function);
  for (const f of syms.functions) add(f, CompletionItemKind.Function);
  for (const c of syms.classes) add(c, CompletionItemKind.Class);
  for (const v of syms.constants) add(v, CompletionItemKind.Variable);
  for (const ns of Object.keys(syms.namespaceMembers)) add(ns, CompletionItemKind.Module);
  return items;
}

function resolveNamespace(syms, receiver) {
  const parts = receiver.split(".");
  for (let start = 0; start < parts.length; start++) {
    let node = syms.namespaceMembers[parts[start]];
    if (!node) continue;
    let ok = true;
    for (let k = start + 1; k < parts.length; k++) {
      node = node.namespaceMembers && node.namespaceMembers[parts[k]];
      if (!node) { ok = false; break; }
    }
    if (ok) return node;
  }
  return null;
}

function addHeaderSymbols(syms, bd) {
  let files;
  try {
    files = fs.readdirSync(bd);
  } catch (e) {
    return;
  }
  for (const f of files) {
    if (!f.toLowerCase().endsWith(".kosh")) continue;
    const full = path.join(bd, f);
    let hs;
    try {
      hs = collectSymbols(fs.readFileSync(full, "utf8"), bd);
    } catch (e) {
      continue;
    }
    for (const x of hs.functions) pushUnique(syms.functions, x);
    for (const x of hs.classes) pushUnique(syms.classes, x);
    for (const x of hs.constants) pushUnique(syms.constants, x);
    for (const [k, v] of Object.entries(hs.members)) {
      if (!syms.members[k]) syms.members[k] = v;
    }
    for (const [k, v] of Object.entries(hs.parents)) {
      if (!syms.parents[k]) syms.parents[k] = v;
    }
    for (const [k, v] of Object.entries(hs.namespaceMembers)) {
      if (!syms.namespaceMembers[k]) syms.namespaceMembers[k] = v;
    }
    for (const [k, v] of Object.entries(hs.instantiations)) {
      syms.instantiations[k] = v;
    }
    // expose the header by its module name (as `import "utils"` would)
    const modName = f.replace(/\.kosh$/i, "");
    if (/^[A-Za-z_][A-Za-z0-9_]*$/.test(modName) && !syms.namespaceMembers[modName]) {
      syms.namespaceMembers[modName] = hs;
    }
  }
}

connection.onDocumentSymbol(params => {
  const doc = documents.get(params.textDocument.uri);
  const text = doc ? doc.getText() : "";
  const syms = collectSymbols(text, baseDir(params.textDocument.uri));
  const symbols = [];
  for (const d of syms.declarations) {
    const range = {
      start: { line: d.line, character: d.character },
      end: { line: d.line, character: d.character + d.name.length },
    };
    symbols.push({
      name: d.name,
      kind: SYMBOL_KINDS[d.kind] || SYMBOL_KINDS.variable,
      range,
      selectionRange: range,
    });
  }
  return symbols;
});

function baseDir(uri) {
  try {
    if (!uri || !uri.startsWith("file:")) return process.cwd();
    return path.dirname(fileURLToPath(uri));
  } catch (e) {
    return process.cwd();
  }
}

documents.listen(connection);
connection.listen();
