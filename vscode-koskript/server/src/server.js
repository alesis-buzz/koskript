const { createConnection, TextDocuments, ProposedFeatures, TextDocumentSyncKind, CompletionItemKind } = require("vscode-languageserver/node");
const { TextDocument } = require("vscode-languageserver-textdocument");
const { parse, collectSymbols } = require("./parser");
const path = require("path");
const fs = require("fs");

const connection = createConnection(process.stdin, process.stdout);
const documents = new TextDocuments(TextDocument);

const KEYWORDS = ["let","const","fun","wrapper","class","extends","namespace","error","import","as","if","elseif","else","while","for","foreach","return","break","continue","throw","try","catch","finally","static","public","private","this","super","new","true","false","null","and","or","not","in"];
const BUILTINS = ["print","len","type","typeof","str","int","float","bool","range","copy","array","map","string","bytes","math","json"];
const STDLIB_MEMBERS = {
  "array": ["push","pop","insert","remove_at","clear","sort","sort_by","reverse","slice","join","index_of","contains","map","filter","reduce","each"],
  "map": ["keys","values","has","remove","merge"],
  "string": ["upper","lower","trim","repeat","slice","replace","split","join","reverse","index_of","contains","starts_with","ends_with"],
  "bytes": ["from_array","to_array","from_hex","to_hex","compare","index_of","contains","slice"],
  "math": ["sqrt","pow","abs","floor","ceil","round","min","max","random","sin","cos","tan","atan","atan2","exp","log","PI","E"],
  "json": ["encode","decode"],
};


documents.onDidChangeContent(change => {
  validate(change.document);
});

documents.onDidOpen(event => {
  validate(event.document);
});

function validate(doc) {
  const text = doc.getText();
  const diagnostics = [];
  try {
    parse(text);
  } catch (e) {
    diagnostics.push({
      severity: 1,
      range: { start: { line: 0, character: 0 }, end: { line: 0, character: 1 } },
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
  const doc = documents.get(params.textDocument.uri);
  const text = doc ? doc.getText() : "";
  const bd = baseDir(params.textDocument.uri);
  const syms = collectSymbols(text, bd);
  // include .kosh headers in the same directory
  try {
    for (const f of fs.readdirSync(bd)) {
      if (!f.toLowerCase().endsWith(".kosh")) continue;
      const full = path.join(bd, f);
      const code = fs.readFileSync(full, "utf8");
      const hs = collectSymbols(code, bd);
      for (const x of hs.functions) syms.functions.push(x);
      for (const x of hs.classes) syms.classes.push(x);
      for (const x of hs.constants) syms.constants.push(x);
      for (const [k, v] of Object.entries(hs.members)) {
        if (!syms.members[k]) syms.members[k] = v;
      }
      for (const [k, v] of Object.entries(hs.parents)) {
        if (!syms.parents[k]) syms.parents[k] = v;
      }
      for (const [k, v] of Object.entries(hs.namespaceMembers)) {
        if (!syms.namespaceMembers[k]) syms.namespaceMembers[k] = v;
      }
      // expose the header by its module name (as `import "utils"` would)
      const modName = f.replace(/\.kosh$/i, "");
      if (modName && !syms.namespaceMembers[modName]) syms.namespaceMembers[modName] = hs;
      for (const [k, v] of Object.entries(hs.instantiations)) {
        syms.instantiations[k] = v;
      }
    }
  } catch (e) {}

  const pos = params.position;
  const line = text.split("\n")[pos.line] || "";
  const before = line.slice(0, pos.character);

  // `receiver.` or `receiver::` (optionally with a typed prefix)
  const m = /([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)(::|\.)([A-Za-z0-9_]*)$/.exec(before);
  if (m) {
    let receiver = m[1];
    const sep = m[2];
    const partial = m[3];
    const items = [];
    const add = (label, kind) => {
      if (!partial || label.startsWith(partial)) {
        if (!items.some(i => i.label === label)) items.push({ label, kind });
      }
    };

    // walk `extends` chains for class members
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

    let resolved = true;
    if (STDLIB_MEMBERS[receiver]) {
      for (const fn of STDLIB_MEMBERS[receiver]) {
        if (sep === "::") continue;
        if (/^[A-Z]/.test(fn)) add(fn, CompletionItemKind.Constant);
        else add(fn, CompletionItemKind.Function);
      }
    } else if (syms.namespaceMembers[receiver] || (receiver.includes(".") && syms.namespaceMembers[receiver.split(".").pop()])) {
      const aliasKey = receiver.split(".").pop();
      const ns = syms.namespaceMembers[aliasKey] || syms.namespaceMembers[receiver];
      for (const f of ns.functions) add(f, CompletionItemKind.Function);
      for (const c of ns.classes) add(c, CompletionItemKind.Class);
      for (const v of ns.constants) add(v, CompletionItemKind.Variable);
    } else if (syms.instantiations[receiver]) {
      for (const mm of getMembers(syms.instantiations[receiver])) {
        add(mm.name, mm.kind === "field" ? CompletionItemKind.Field : CompletionItemKind.Method);
      }
    } else if (syms.members[receiver]) {
      for (const mm of getMembers(receiver)) {
        add(mm.name, mm.kind === "field" ? CompletionItemKind.Field : CompletionItemKind.Method);
      }
    } else {
      resolved = false;
    }

    if (resolved) return items;
  }

  const items = [];
  for (const kw of KEYWORDS) items.push({ label: kw, kind: CompletionItemKind.Keyword });
  for (const b of BUILTINS) items.push({ label: b, kind: CompletionItemKind.Function });
  for (const f of syms.functions) items.push({ label: f, kind: CompletionItemKind.Function });
  for (const c of syms.classes) items.push({ label: c, kind: CompletionItemKind.Class });
  for (const v of syms.constants) items.push({ label: v, kind: CompletionItemKind.Variable });
  return items;
});

connection.onDocumentSymbol(params => {
  const doc = documents.get(params.textDocument.uri);
  const text = doc ? doc.getText() : "";
  const syms = collectSymbols(text, baseDir(params.textDocument.uri));
  const symbols = [];
  for (const f of syms.functions) {
    symbols.push({ name: f, kind: 12, range: emptyRange(), selectionRange: emptyRange() });
  }
  for (const c of syms.classes) {
    symbols.push({ name: c, kind: 5, range: emptyRange(), selectionRange: emptyRange() });
  }
  return symbols;
});

function emptyRange() {
  return { start: { line: 0, character: 0 }, end: { line: 0, character: 0 } };
}

function baseDir(uri) {
  try {
    const fsPath = uri.replace("file://", "");
    return path.dirname(decodeURIComponent(fsPath));
  } catch (e) {
    return process.cwd();
  }
}

documents.listen(connection);
connection.listen();