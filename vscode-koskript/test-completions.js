// End-to-end LSP stdio tests for the Koskript language server.
// Usage: node test-completions.js
const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { pathToFileURL } = require("url");

const SERVER = process.env.KOS_SERVER || path.join(__dirname, "server", "src", "server.js");

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "koskript-lsp-"));
fs.writeFileSync(path.join(tmp, "utils.kosh"), "fun hello(name)\n");
fs.writeFileSync(path.join(tmp, "point.kosh"), [
  "class Point {",
  "    public x = 0",
  "    public fun move(dx, dy)",
  "}",
].join("\n"));

const proc = spawn(process.execPath, [SERVER], { stdio: ["pipe", "pipe", "pipe"] });
proc.stderr.on("data", d => console.error("SRV-ERR", d.toString().slice(0, 1200)));

let buf = Buffer.alloc(0);
let nextId = 1;
const pending = new Map();
const diagnostics = [];

proc.stdout.on("data", chunk => {
  buf = Buffer.concat([buf, chunk]);
  for (;;) {
    const sep = buf.indexOf("\r\n\r\n");
    if (sep < 0) break;
    const header = buf.slice(0, sep).toString();
    const lenMatch = header.match(/Content-Length:\s*(\d+)/i);
    if (!lenMatch) {
      buf = buf.slice(sep + 4);
      continue;
    }
    const len = parseInt(lenMatch[1], 10);
    if (buf.length < sep + 4 + len) break;
    const body = buf.slice(sep + 4, sep + 4 + len).toString();
    buf = buf.slice(sep + 4 + len);
    let msg;
    try { msg = JSON.parse(body); } catch { continue; }
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    } else if (msg.method === "textDocument/publishDiagnostics") {
      diagnostics.push(msg.params);
    }
  }
});

function send(msg) {
  const b = Buffer.from(JSON.stringify(msg));
  proc.stdin.write(`Content-Length: ${b.length}\r\n\r\n${b}`);
}
function request(method, params) {
  const id = nextId++;
  return new Promise(res => {
    pending.set(id, res);
    send({ jsonrpc: "2.0", id, method, params });
  });
}
const notify = (method, params) => send({ jsonrpc: "2.0", method, params });
const wait = ms => new Promise(r => setTimeout(r, ms));

let failures = 0;
function check(name, fn) {
  try {
    fn();
    console.log(`[PASS] ${name}`);
  } catch (e) {
    failures++;
    console.log(`[FAIL] ${name}: ${e.message}`);
  }
}

async function completion(uri, text, version, position) {
  notify("textDocument/didChange", {
    textDocument: { uri, version },
    contentChanges: [{ text }],
  });
  await wait(120);
  const resp = await request("textDocument/completion", {
    textDocument: { uri },
    position,
  });
  const result = resp.result;
  return Array.isArray(result) ? result.map(i => i.label) : [];
}

(async () => {
  await request("initialize", { capabilities: {} });
  notify("initialized", {});

  const base = [
    "class Person {",
    "    public name = \"generic\"",
    "    private energy = 100",
    "    public fun speak() { return \"...\" }",
    "}",
    "class Dog extends Person {",
    "    public fun bark() { return \"woof\" }",
    "}",
    "namespace Utils {",
    "    const MAX = 3",
    "    fun double(x) { return x * 2 }",
    "}",
    "fun top() { return 1 }",
    "let d = new Dog()",
    "let p = new Point(0, 0)",
    "let arr = [1, 2, 3]",
  ];
  const baseText = base.join("\n");
  const baseLines = base.length;
  const uri = pathToFileURL(path.join(tmp, "member.kos")).toString();

  notify("textDocument/didOpen", {
    textDocument: { uri, languageId: "koskript", version: 1, text: "" },
  });
  await wait(80);

  let version = 2;
  const cases = [
    ["d. (instance members + inheritance)", "let h = d.", ["name", "speak", "bark"]],
    ["array.pu (stdlib partial)", "let h = array.pu", ["push"]],
    ["string. (stdlib)", "let h = string.", ["upper", "lower", "split", "find", "pad_left"]],
    ["bytes.from_s (stdlib)", "let h = bytes.from_s", ["from_string"]],
    ["math.cl (stdlib)", "let h = math.cl", ["clamp"]],
    ["math.pi (constant)", "let h = math.pi", ["pi"]],
    ["Dog.ba (class members)", "let h = Dog.ba", ["bark"]],
    ["Utils. (namespace)", "let h = Utils.", ["double", "MAX"]],
    ["utils.kosh header via module name", "let h = utils.h", ["hello"]],
    ["point.kosh class through an instance", "let h = p.mo", ["move"]],
  ];

  for (const [label, line, expected] of cases) {
    const text = baseText + "\n" + line;
    const labels = await completion(uri, text, version++, {
      line: baseLines,
      character: line.length,
    });
    check(label, () => {
      const missing = expected.filter(e => !labels.includes(e));
      if (missing.length) throw new Error("missing " + missing.join(", "));
    });
  }

  // Global completion must not contain methods or namespace members.
  {
    const line = "let h = ";
    const labels = await completion(uri, baseText + "\n" + line, version++, {
      line: baseLines,
      character: line.length,
    });
    check("plain completion includes globals", () => {
      for (const expected of ["let", "print", "top", "Person"]) {
        if (!labels.includes(expected)) throw new Error("missing " + expected);
      }
    });
    check("plain completion does not leak methods or namespace members", () => {
      const leaked = ["speak", "bark", "double"].filter(x => labels.includes(x));
      if (leaked.length) throw new Error("leaked " + leaked.join(", "));
    });
  }

  const thisText = [
    "class Counter {",
    "    private count = 0",
    "    public fun inc() {",
    "        this.",
    "    }",
    "}",
  ].join("\n");
  const thisLabels = await completion(uri, thisText, version++, { line: 3, character: 13 });
  check("this. completes fields and methods", () => {
    for (const expected of ["count", "inc"]) {
      if (!thisLabels.includes(expected)) throw new Error("missing " + expected);
    }
  });

  const bareColonText = [
    "class Counter {",
    "    private count = 0",
    "    public fun inc() {",
    "        ::",
    "    }",
    "}",
  ].join("\n");
  const bareLabels = await completion(uri, bareColonText, version++, { line: 3, character: 10 });
  check("bare :: completes current class members", () => {
    for (const expected of ["count", "inc"]) {
      if (!bareLabels.includes(expected)) throw new Error("missing " + expected);
    }
  });

  const superText = [
    "class Base {",
    "    public fun hello() { return 1 }",
    "}",
    "class Child extends Base {",
    "    public fun hi() {",
    "        super::",
    "    }",
    "}",
  ].join("\n");
  const superLabels = await completion(uri, superText, version++, { line: 5, character: 15 });
  check("super:: completes parent members", () => {
    if (!superLabels.includes("hello")) throw new Error("missing hello");
  });

  // Diagnostics: a valid file must be clean, an invalid one must point at the
  // offending position instead of always line 0.
  const validText = [
    "let b = b\"hi\"",
    "let m = { \"a\"= 1 }",
    "class A {",
    "    @loud",
    "    public fun p() { return 1 }",
    "}",
  ].join("\n");
  notify("textDocument/didChange", {
    textDocument: { uri, version: version++ },
    contentChanges: [{ text: validText }],
  });
  await wait(150);
  const validDiag = diagnostics.filter(d => d.uri === uri).pop();
  check("valid code produces no diagnostics", () => {
    if (!validDiag) throw new Error("no diagnostics notification");
    if (validDiag.diagnostics.length) {
      throw new Error(validDiag.diagnostics.map(d => d.message).join("; "));
    }
  });

  notify("textDocument/didChange", {
    textDocument: { uri, version: version++ },
    contentChanges: [{ text: "let x = " }],
  });
  await wait(150);
  const invalidDiag = diagnostics.filter(d => d.uri === uri).pop();
  check("syntax error points at the real position", () => {
    if (!invalidDiag || !invalidDiag.diagnostics.length) throw new Error("no diagnostic");
    const range = invalidDiag.diagnostics[0].range;
    if (range.start.line !== 0 || range.start.character !== 8) {
      throw new Error(`got ${range.start.line}:${range.start.character}, expected 0:8`);
    }
  });

  const headerUri = pathToFileURL(path.join(tmp, "header.kosh")).toString();
  notify("textDocument/didOpen", {
    textDocument: { uri: headerUri, languageId: "koskript", version: 1, text: "fun add(a, b)\nclass Point {\n    public fun move(dx, dy)\n}\n" },
  });
  await wait(150);
  const headerDiag = diagnostics.filter(d => d.uri === headerUri).pop();
  check(".kosh headers allow bodyless declarations", () => {
    if (!headerDiag) throw new Error("no diagnostics notification");
    if (headerDiag.diagnostics.length) {
      throw new Error(headerDiag.diagnostics.map(d => d.message).join("; "));
    }
  });

  const bodylessUri = pathToFileURL(path.join(tmp, "bodyless.kos")).toString();
  notify("textDocument/didOpen", {
    textDocument: { uri: bodylessUri, languageId: "koskript", version: 1, text: "fun add(a, b)\n" },
  });
  await wait(150);
  const bodylessDiag = diagnostics.filter(d => d.uri === bodylessUri).pop();
  check(".kos files require function bodies", () => {
    if (!bodylessDiag || !bodylessDiag.diagnostics.length) throw new Error("no diagnostic");
    if (!/Expected \{/.test(bodylessDiag.diagnostics[0].message)) {
      throw new Error("unexpected message: " + bodylessDiag.diagnostics[0].message);
    }
  });

  // Document symbols carry real ranges.
  const symbolText = "fun alpha() { return 1 }\nclass Beta {}\nconst GAMMA = 1\n";
  notify("textDocument/didChange", {
    textDocument: { uri, version: version++ },
    contentChanges: [{ text: symbolText }],
  });
  await wait(120);
  const symbols = (await request("textDocument/documentSymbol", {
    textDocument: { uri },
  })).result || [];
  check("document symbols have real ranges", () => {
    const alpha = symbols.find(s => s.name === "alpha");
    const beta = symbols.find(s => s.name === "Beta");
    const gamma = symbols.find(s => s.name === "GAMMA");
    if (!alpha || !beta || !gamma) throw new Error("missing symbols");
    if (alpha.range.start.line !== 0) throw new Error("alpha line " + alpha.range.start.line);
    if (beta.range.start.line !== 1) throw new Error("beta line " + beta.range.start.line);
    if (gamma.range.start.line !== 2) throw new Error("gamma line " + gamma.range.start.line);
    if (alpha.kind !== 12 || beta.kind !== 5 || gamma.kind !== 14) {
      throw new Error(`kinds ${alpha.kind}/${beta.kind}/${gamma.kind}`);
    }
  });

  proc.kill();
  fs.rmSync(tmp, { recursive: true, force: true });

  if (failures) {
    console.error(`\n${failures} completion test(s) failed`);
    process.exit(1);
  }
  console.log("\nAll completion tests passed");
})().catch(err => {
  console.error(err);
  proc.kill();
  process.exit(1);
});
