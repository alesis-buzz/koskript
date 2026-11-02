const vscode = require("vscode");
const { LanguageClient, TransportKind } = require("vscode-languageclient/node");
const path = require("path");

let client;

function activate(context) {
  const outputChannel = vscode.window.createOutputChannel("Koskript Language Server");
  context.subscriptions.push(outputChannel);

  const serverModule = context.asAbsolutePath(path.join("server", "src", "server.js"));
  // `module` + `cp.fork` makes the client use the Node runtime bundled with
  // VS Code (ELECTRON_RUN_AS_NODE), so the extension does not depend on a
  // `node` executable being installed or on PATH.
  const serverOptions = {
    run: { module: serverModule, transport: TransportKind.stdio },
    debug: { module: serverModule, transport: TransportKind.stdio }
  };
  const clientOptions = {
    documentSelector: [{ language: "koskript" }],
    outputChannel
  };

  client = new LanguageClient("koskript", "Koskript Language Server", serverOptions, clientOptions);
  client.start().then(
    () => outputChannel.appendLine("Koskript language server started"),
    err => {
      outputChannel.appendLine("Failed to start the Koskript language server:");
      outputChannel.appendLine(String(err && err.stack ? err.stack : err));
      outputChannel.show(true);
    }
  );
}

function deactivate() {
  if (client) {
    const stopped = client.stop();
    client = undefined;
    return stopped;
  }
}

module.exports = { activate, deactivate };
