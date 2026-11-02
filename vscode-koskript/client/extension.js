const vscode = require("vscode");
const { LanguageClient, TransportKind } = require("vscode-languageclient/node");
const path = require("path");

let client;

function activate(context) {
  const outputChannel = vscode.window.createOutputChannel("Koskript Language Server");
  context.subscriptions.push(outputChannel);
  const serverModule = context.asAbsolutePath(path.join("server", "src", "server.js"));
  const serverOptions = {
    run: { command: "node", args: [serverModule], transport: TransportKind.stdio },
    debug: { command: "node", args: [serverModule], transport: TransportKind.stdio }
  };
  const clientOptions = {
    documentSelector: [{ scheme: "file", language: "koskript" }],
    outputChannel
  };
  client = new LanguageClient("koskript", "Koskript Language Server", serverOptions, clientOptions);
  client.start().then(() => outputChannel.appendLine("started")).catch(err => outputChannel.appendLine(String(err)));
}

function deactivate() {
  if (client) {
    return client.stop();
  }
}

module.exports = { activate, deactivate };
