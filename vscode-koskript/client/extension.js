const { LanguageClient, TransportKind } = require("vscode-languageclient/node");
const path = require("path");

let client;

function activate(context) {
  const serverModule = context.asAbsolutePath(path.join("server", "src", "server.js"));
  const serverOptions = {
    run: { module: serverModule, transport: TransportKind.ipc },
    debug: { module: serverModule, transport: TransportKind.ipc }
  };
  const clientOptions = {
    documentSelector: [{ scheme: "file", language: "koskript" }]
  };
  client = new LanguageClient("koskript", "Koskript Language Server", serverOptions, clientOptions);
  client.start();
}

function deactivate() {
  if (client) {
    return client.stop();
  }
}

module.exports = { activate, deactivate };