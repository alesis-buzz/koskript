// Tests for project-wide header discovery (headers.js).
// Usage: node test-headers.js
const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { HeaderIndex } = require("./server/src/headers");
const { collectSymbols } = require("./server/src/parser");

let failures = 0;
function check(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); }
  catch (e) { failures++; console.log(`[FAIL] ${name}: ${e.message}`); }
}

function makeProject() {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "koskript-hdr-"));
  fs.mkdirSync(path.join(tmp, "modules"), { recursive: true });
  fs.mkdirSync(path.join(tmp, "headers"), { recursive: true });
  fs.writeFileSync(path.join(tmp, "root.kosh"), "fun root_fn(x)\nconst ROOT_CONST = 1\n");
  fs.writeFileSync(path.join(tmp, "modules", "deep.kosh"), "class Deep {\n    public fun go()\n}\n");
  fs.writeFileSync(path.join(tmp, "headers", "util.kosh"), "namespace Util {\n    fun double(x)\n}\n");
  return tmp;
}

function merge(syms, entries) {
  for (const entry of entries) {
    const hs = entry.symbols;
    for (const x of hs.functions) if (!syms.functions.includes(x)) syms.functions.push(x);
    for (const x of hs.classes) if (!syms.classes.includes(x)) syms.classes.push(x);
    for (const x of hs.constants) if (!syms.constants.includes(x)) syms.constants.push(x);
    for (const [k, v] of Object.entries(hs.members)) if (!syms.members[k]) syms.members[k] = v;
    for (const [k, v] of Object.entries(hs.parents)) if (!syms.parents[k]) syms.parents[k] = v;
    for (const [k, v] of Object.entries(hs.namespaceMembers)) if (!syms.namespaceMembers[k]) syms.namespaceMembers[k] = v;
    for (const [k, v] of Object.entries(hs.instantiations)) syms.instantiations[k] = v;
    if (/^[A-Za-z_][A-Za-z0-9_]*$/.test(entry.moduleName) && !syms.namespaceMembers[entry.moduleName]) {
      syms.namespaceMembers[entry.moduleName] = hs;
    }
  }
}

// Project-wide discovery: headers anywhere in the project are visible from a
// script living in a nested folder.
{
  const tmp = makeProject();
  const idx = new HeaderIndex();
  idx.setRoots([tmp]);
  const doc = path.join(tmp, "modules", "app.kos");
  const entries = idx.entriesFor(doc);
  check("discovers every header in the project", () => {
    const rels = entries.map(e => e.relPath).sort();
    assert.deepStrictEqual(rels, ["headers/util.kosh", "modules/deep.kosh", "root.kosh"].sort());
  });
  check("nearest header comes first", () => {
    assert.strictEqual(entries[0].relPath, "modules/deep.kosh");
  });
  const syms = collectSymbols("let x = new Deep()\n", path.join(tmp, "modules"), undefined, idx.resolverFor(doc));
  merge(syms, entries);
  check("merges classes from a sibling header", () => assert.ok(syms.classes.includes("Deep")));
  check("merges functions from the project root", () => assert.ok(syms.functions.includes("root_fn")));
  check("merges constants from the project root", () => assert.ok(syms.constants.includes("ROOT_CONST")));
  check("merges namespaces from a nested headers folder", () => {
    assert.ok(syms.namespaceMembers.Util);
    assert.deepStrictEqual(syms.namespaceMembers.Util.functions, ["double"]);
  });
  check("exposes headers by module name", () => {
    assert.ok(syms.namespaceMembers.deep);
    assert.ok(syms.namespaceMembers.util);
  });
  check("resolves a root header by basename from a nested file", () => {
    assert.strictEqual(idx.resolverFor(doc)("root", path.join(tmp, "modules")), path.join(tmp, "root.kosh"));
  });
  check("resolves a header by relative path from a nested file", () => {
    assert.strictEqual(idx.resolverFor(doc)("modules/deep", path.join(tmp, "modules")), path.join(tmp, "modules", "deep.kosh"));
  });
  check("resolves a header by basename anywhere in the project", () => {
    assert.strictEqual(idx.resolverFor(doc)("util", path.join(tmp, "modules")), path.join(tmp, "headers", "util.kosh"));
  });
  fs.rmSync(tmp, { recursive: true, force: true });
}

// Fallback without a workspace folder: discovery walks up to the project root.
{
  const tmp = makeProject();
  const idx = new HeaderIndex();
  // no setRoots -> fallback
  const doc = path.join(tmp, "modules", "app.kos");
  const entries = idx.entriesFor(doc);
  check("fallback discovers headers without a workspace root", () => {
    assert.ok(entries.length === 3, "got " + entries.length);
    assert.ok(entries.some(e => e.relPath === "root.kosh"));
  });
  fs.rmSync(tmp, { recursive: true, force: true });
}

// Duplicate module names: the nearest header wins.
{
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "koskript-dup-"));
  fs.mkdirSync(path.join(tmp, "modules"), { recursive: true });
  fs.writeFileSync(path.join(tmp, "util.kosh"), "fun util() { return \"far\" }\n");
  fs.writeFileSync(path.join(tmp, "modules", "util.kosh"), "fun util() { return \"near\" }\n");
  const idx = new HeaderIndex();
  idx.setRoots([tmp]);
  const doc = path.join(tmp, "modules", "app.kos");
  const entries = idx.entriesFor(doc);
  check("duplicate names: nearest entry first", () => {
    assert.strictEqual(entries[0].path, path.join(tmp, "modules", "util.kosh"));
  });
  fs.rmSync(tmp, { recursive: true, force: true });
}

// Open (unsaved) header edits are served from memory.
{
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "koskript-open-"));
  const header = path.join(tmp, "live.kosh");
  fs.writeFileSync(header, "fun old_name()\n");
  const idx = new HeaderIndex();
  idx.setRoots([tmp]);
  idx.setTextProvider(p => p === header ? "fun new_name()\n" : null);
  idx.invalidate();
  const entries = idx.entriesFor(path.join(tmp, "app.kos"));
  const names = entries.flatMap(e => e.symbols.functions);
  check("open header edits are visible before saving", () => {
    assert.ok(names.includes("new_name"), "new_name missing");
    assert.ok(!names.includes("old_name"), "old_name leaked");
  });
  fs.rmSync(tmp, { recursive: true, force: true });
}

if (failures) {
  console.error(`\n${failures} header test(s) failed`);
  process.exit(1);
}
console.log("\nAll header tests passed");
