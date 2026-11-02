// Parses every ```koskript block in the documentation with the LSP parser, so
// the editor never flags a documented example as invalid.
// Usage: node test-docs.js
const fs = require("fs");
const path = require("path");
const { parse } = require("./server/src/parser");

const docsDir = path.join(__dirname, "..", "docs", "docs");
const files = fs.readdirSync(docsDir).filter(f => f.endsWith(".md"));

let failures = 0;
for (const file of files) {
  const text = fs.readFileSync(path.join(docsDir, file), "utf8");
  const re = /```koskript\r?\n([\s\S]*?)```/g;
  let match;
  let index = 0;
  let failed = 0;
  while ((match = re.exec(text)) !== null) {
    index++;
    try {
      parse(match[1]);
    } catch (strictError) {
      try {
        // Header examples in the docs are bodyless by design.
        parse(match[1], { allowBodyless: true });
      } catch (e) {
        failed++;
        failures++;
        console.log(`[FAIL] ${file} block ${index}: ${e.message} (line ${e.line}:${e.character})`);
      }
    }
  }
  console.log(`[${failed ? "FAIL" : "PASS"}] ${file}: ${index - failed}/${index} blocks parse`);
}

if (failures) {
  console.error(`\n${failures} documentation block(s) failed to parse`);
  process.exit(1);
}
console.log("\nAll documentation blocks parse");
