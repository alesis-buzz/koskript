const { createConnection, TextDocuments, ProposedFeatures, TextDocumentSyncKind, CompletionItemKind } = require("vscode-languageserver/node");
const { TextDocument } = require("vscode-languageserver-textdocument");
const { parse, collectSymbols } = require("./parser");

const connection = createConnection(ProposedFeatures.all);
const documents = new TextDocuments(TextDocument);

const KEYWORDS = ["let","const","fun","wrapper","class","extends","namespace","error","import","as","if","elseif","else","while","for","foreach","return","break","continue","throw","try","catch","finally","static","public","private","this","super","new","true","false","null","and","or","not","in"];
const BUILTINS = ["print","len","type","typeof","str","int","float","bool","range","copy"];

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
  const syms = collectSymbols(text);
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
  const syms = collectSymbols(text);
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

documents.listen(connection);
connection.listen();