// Unit tests for the Koskript language server parser and symbol collector.
// Usage: node test-parser.js
const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { parse, collectSymbols, enclosingClass } = require("./server/src/parser");

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

const validSnippets = {
  "bytes literal": 'let b = b"hi"',
  "bytes literal in call": 'print(bytes.to_string(b"\\xc3\\xb1"))',
  "bytes literal with quotes": 'let b = B\'a\\\'b\'',
  "map with equals": 'let m = { "a"= 1, b= 2 }',
  "decorated method": 'class A {\n  @loud\n  public fun ping() { return "pong" }\n}',
  "decorated method with args": 'class A {\n  @log("x")\n  static fun ping() { return 1 }\n}',
  "decorated function": '@loud\nfun greet(name) { return "hola " + name }',
  "namespace and class": "namespace Utils {\n  const MAX = 3\n  fun double(x) { return x * 2 }\n  class Point {\n    public x = 0\n    constructor(x) { this.x = x }\n  }\n}",
  "super constructor": 'class D extends A {\n  constructor(n) { super::constructor(n) }\n}',
  "error definition": 'error HttpError (err, status) {\n  err.message = "failed"\n  err.status = status\n}',
  "qualified new": "print(new Utils.Point(1).x)",
  "lambdas": 'let add = (a, b) { return a + b }\nlet zero = () { return 0 }',
  "index and unary minus": "let x = [1, 2][-1]",
};

for (const [name, code] of Object.entries(validSnippets)) {
  check(`parse ${name}`, () => parse(code));
}

check("parse bodyless header with allowBodyless", () => {
  parse("fun add(a, b)\nclass Point {\n  public fun move(dx, dy)\n}", { allowBodyless: true });
});

check("reject a bodyless function in a .kos file", () => {
  assert.throws(() => parse("fun add(a, b)"), /Expected \{/);
});

check("reject map with colon (matches the Python runtime)", () => {
  assert.throws(() => parse('let m = { "a": 1 }'), /Expected =/);
});

check("reports the error position", () => {
  try {
    parse("let x = \nlet y = 1");
    throw new Error("expected a syntax error");
  } catch (e) {
    assert.strictEqual(e.line, 1);
    assert.strictEqual(e.character, 0);
  }
});

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "koskript-lsp-"));
fs.writeFileSync(path.join(tmp, "utils.kosh"), [
  "fun hello(name)",
  "const VERSION = 1",
].join("\n"));
fs.writeFileSync(path.join(tmp, "point.kosh"), [
  "class Point {",
  "    public x = 0",
  "    public fun move(dx, dy)",
  "}",
].join("\n"));

const source = [
  "import \"utils\"",
  "import \"point\"",
  "const TOP = 1",
  "fun top() {",
  "    let local = 1",
  "    fun nested() { return local }",
  "}",
  "namespace Utils {",
  "    fun double(x) { return x * 2 }",
  "}",
  "class Person {",
  "    public name = \"generic\"",
  "    private energy = 100",
  "    public fun speak() { return \"...\" }",
  "}",
  "class Dog extends Person {",
  "    public fun bark() { return \"woof\" }",
  "}",
  "let d = new Dog()",
  "let p = new Point(0, 0)",
].join("\n");

const syms = collectSymbols(source, tmp);

check("collects top-level functions", () => {
  assert.ok(syms.functions.includes("top"), "top missing");
  assert.ok(!syms.functions.includes("Dog"), "class leaked into functions");
  assert.ok(syms.classes.includes("Person"), "Person missing");
  assert.ok(syms.classes.includes("Dog"), "Dog missing");
  assert.ok(syms.constants.includes("TOP"), "TOP missing");
});

check("does not leak method names into globals", () => {
  assert.ok(!syms.functions.includes("speak"), "speak leaked");
  assert.ok(!syms.functions.includes("bark"), "bark leaked");
  assert.ok(!syms.functions.includes("nested"), "nested leaked");
});

check("does not leak namespace members into globals", () => {
  assert.ok(!syms.functions.includes("double"), "double leaked");
  assert.ok(syms.namespaceMembers.Utils, "namespace missing");
  assert.ok(syms.namespaceMembers.Utils.functions.includes("double"));
});

check("collects class fields and methods", () => {
  const person = syms.members.Person || [];
  assert.ok(person.some(m => m.name === "name" && m.kind === "field"), "name field missing");
  assert.ok(person.some(m => m.name === "energy" && m.kind === "field"), "energy field missing");
  assert.ok(person.some(m => m.name === "speak" && m.kind === "method"), "speak method missing");
  assert.strictEqual(syms.parents.Dog, "Person");
});

check("collects instantiations", () => {
  assert.strictEqual(syms.instantiations.d, "Dog");
  assert.strictEqual(syms.instantiations.p, "Point");
});

check("resolves imports", () => {
  assert.ok(syms.namespaceMembers.utils, "module alias missing");
  assert.ok(syms.namespaceMembers.utils.functions.includes("hello"));
  assert.ok(syms.functions.includes("utils.hello"), "prefixed import missing");
  assert.ok(syms.constants.includes("utils.VERSION"));
});

check("merges imported class members", () => {
  const point = syms.members.Point || [];
  assert.ok(point.some(m => m.name === "move" && m.kind === "method"), "move missing");
  assert.ok(point.some(m => m.name === "x" && m.kind === "field"), "x missing");
});

check("resolves namespaces through dotted receivers", () => {
  const nested = collectSymbols("namespace App {\n  namespace Utils {\n    fun f() {}\n  }\n}");
  assert.ok(nested.namespaceMembers.App.namespaceMembers.Utils.functions.includes("f"));
});

check("finds the enclosing class", () => {
  const code = "class Counter {\n    public fun inc() {\n        this.\n    }\n}";
  const offset = code.indexOf("this.") + "this.".length;
  assert.strictEqual(enclosingClass(code, offset), "Counter");
});

check("does not report a class outside its body", () => {
  const code = "class Counter {\n    public fun inc() { return 1 }\n}\nthis.";
  const offset = code.lastIndexOf("this.") + 5;
  assert.strictEqual(enclosingClass(code, offset), null);
});

fs.rmSync(tmp, { recursive: true, force: true });

if (failures) {
  console.error(`\n${failures} parser test(s) failed`);
  process.exit(1);
}
console.log("\nAll parser tests passed");
