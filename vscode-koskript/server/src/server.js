const { createConnection, TextDocuments, ProposedFeatures, TextDocumentSyncKind, CompletionItemKind } = require("vscode-languageserver/node");
const { TextDocument } = require("vscode-languageserver-textdocument");
const { parse, collectSymbols } = require("./parser");
const path = require("path");
const fs = require("fs");

const connection = createConnection(ProposedFeatures.all);
const documents = new TextDocuments(TextDocument);

const KEYWORDS = ["let","const","fun","wrapper","class","extends","namespace","error","import","as","if","elseif","else","while","for","foreach","return","break","continue","throw","try","catch","finally","static","public","private","this","super","new","true","false","null","and","or","not","in"];
const BUILTINS = ["print","len","type","typeof","str","int","float","bool","range","copy","array","map","string","bytes","math","json"];

documents.onDidChangeContent(change => {
  validate(change.document);
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
    }
  } catch (e) {}
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