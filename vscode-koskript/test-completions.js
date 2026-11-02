// Minimal LSP stdio test client for the Koskript language server.
// Usage: node test-completions.js
const { spawn } = require("child_process");
const path = require("path");

const SERVER = path.join(__dirname, "server", "src", "server.js");
const BASE = process.env.KOS_BASE || process.cwd();
const proc = spawn("node", [SERVER], { stdio: ["pipe", "pipe", "pipe"] });
proc.stderr.on("data", d => console.error("SRV-ERR", d.toString().slice(0, 1200)));

let buf = Buffer.alloc(0);
const pending = new Map();
proc.stdout.on("data", chunk => {
  buf = Buffer.concat([buf, chunk]);
  for (;;) {
    const sep = buf.indexOf("\r\n\r\n");
    if (sep < 0) break;
    const len = parseInt(buf.slice(0, sep).toString().match(/Content-Length: (\d+)/)?.[1] || "0");
    if (!len) break;
    if (buf.length < sep + 4 + len) break;
    const body = buf.slice(sep + 4, sep + 4 + len);
    buf = buf.slice(sep + 4 + len);
    let msg; try { msg = JSON.parse(body.toString()); } catch { continue; }
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    }
  }
});

function send(msg) {
  const b = Buffer.from(JSON.stringify(msg));
  proc.stdin.write(`Content-Length: ${b.length}\r\n\r\n${b}`);
}
function request(id, method, params) {
  return new Promise(res => {
    pending.set(id, res);
    send({ jsonrpc: "2.0", id, method, params });
  });
}
const notify = (method, params) => send({ jsonrpc: "2.0", method, params });

(async () => {
  await request(1, "initialize", { capabilities: {} });
  notify("initialized", {});

  const base = BASE;
  const uri = "file://" + path.join(base, "member.kos");
  notify("textDocument/didOpen", {
    textDocument: { uri, languageId: "koskript", version: 1, text: "" },
  });

  const header = [
    "class Person {",
    "    public fun name()",
    "    public fun speak()",
    "    private fun secret()",
    "}",
    "class Dog extends Person {",
    "    public fun bark()",
    "}",
    "let d = new Dog(\"Rex\")",
    "let arr = [1, 2, 3]",
  ];

  const cases = [
    // [label, extras after header, cursor line offset, character, expected labels]
    ["d. (instance member, inherits Person)", ["let h = d."], 0, 10, ["name", "speak", "bark"]],
    ["array.pu (stdlib + partial)", ["let h = array.pu"], 0, 14, ["push"]],
    ["string. (stdlib full)", ["let h = string."], 0, 15, ["upper", "lower", "split"]],
    ["Dog. (class statics)", ["let h = Dog.ba"], 0, 14, ["bark"]],
    ["utils.kosh header via module name", ["let h = utils.h"], 0, 14, ["hello"]],
    ["point.h uses .kosh class", ["let h = p.mo"], 0, 12, ["move"]],
    ["plain completion (no dot)", ["let h = "], 0, 8, null],
  ];

  for (const [label, extras, extraLine, character, expect] of cases) {
    const text = header.concat(extras).join("\n") + "\n";
    const line = header.length + extraLine;
    notify("textDocument/didChange", {
      textDocument: { uri, version: 2 },
      contentChanges: [{ text }],
    });
    await new Promise(r => setTimeout(r, 80));
    const resp = await request(Date.now(), "textDocument/completion", {
      textDocument: { uri },
      position: { line, character },
    });
    const got = Array.isArray(resp.result) ? resp.result.map(i => i.label) : resp.result;
    let ok = "?";
    if (expect) {
      const missing = expect.filter(e => !got.includes(e));
      ok = missing.length === 0 ? "PASS" : "FAIL missing " + missing.join(",");
    } else {
      ok = got.length + " items" + (got.length ? " e.g. " + got.slice(0, 5).join(",") : " (EMPTY!)");
    }
    console.log(`[${ok}] ${label}`);
  }
  proc.kill();
})();
