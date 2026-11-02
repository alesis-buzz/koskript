const fs = require("fs");
const path = require("path");

const RESERVED = new Set([
  "if","elseif","else","while","for","foreach","fun","wrapper","return","let","const",
  "true","false","null","and","or","not","in","break","continue","class","extends","new",
  "static","public","private","this","super","constructor","import","as","error","throw",
  "try","catch","finally","namespace"
]);

class KoskriptSyntaxError extends Error {
  constructor(message, line, character) {
    super(message);
    this.name = "KoskriptSyntaxError";
    this.line = line;
    this.character = character;
  }
}

function lineStartsOf(code) {
  const starts = [0];
  for (let i = 0; i < code.length; i++) {
    if (code[i] === "\n") starts.push(i + 1);
  }
  return starts;
}

function positionAt(starts, offset) {
  let lo = 0;
  let hi = starts.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (starts[mid] <= offset) lo = mid;
    else hi = mid - 1;
  }
  return { line: lo, character: offset - starts[lo] };
}

function scanString(code, quotePos, fail) {
  const quote = code[quotePos];
  let pos = quotePos + 1;
  while (pos < code.length && code[pos] !== quote) {
    if (code[pos] === "\\") pos++;
    pos++;
  }
  if (pos >= code.length) fail(quotePos, "Unterminated string literal.");
  return pos + 1;
}

function tokenize(code) {
  const starts = lineStartsOf(code);
  const tokens = [];
  const fail = (offset, message) => {
    const p = positionAt(starts, offset);
    throw new KoskriptSyntaxError(message, p.line, p.character);
  };
  const push = (type, value, offset) => {
    const p = positionAt(starts, offset);
    tokens.push({ type, value, offset, line: p.line, character: p.character });
  };

  let pos = 0;
  while (pos < code.length) {
    const ch = code[pos];
    if (/\s/.test(ch)) { pos++; continue; }
    if (ch === "/" && code[pos + 1] === "/") {
      while (pos < code.length && code[pos] !== "\n") pos++;
      continue;
    }
    if (ch === "/" && code[pos + 1] === "*") {
      fail(pos, "Block comments are not supported, use // for a line comment.");
    }
    if (/[0-9]/.test(ch)) {
      const start = pos;
      while (pos < code.length && /[0-9]/.test(code[pos])) pos++;
      if (code[pos] === "." && /[0-9]/.test(code[pos + 1] || "")) {
        pos++;
        while (pos < code.length && /[0-9]/.test(code[pos])) pos++;
      }
      push("NUMBER", code.slice(start, pos), start);
      continue;
    }
    if (ch === '"' || ch === "'") {
      const start = pos;
      pos = scanString(code, pos, fail);
      push("STRING", code.slice(start, pos), start);
      continue;
    }
    // Bytes literals share the STRING token: `b"..."` / `B'...'`.
    if ((ch === "b" || ch === "B") && (code[pos + 1] === '"' || code[pos + 1] === "'")) {
      const start = pos;
      pos = scanString(code, pos + 1, fail);
      push("STRING", code.slice(start, pos), start);
      continue;
    }
    if (/[a-zA-Z_]/.test(ch)) {
      const start = pos;
      while (pos < code.length && /[a-zA-Z0-9_]/.test(code[pos])) pos++;
      const word = code.slice(start, pos);
      push(RESERVED.has(word) ? word.toUpperCase() : "NAME", word, start);
      continue;
    }
    const two = code.slice(pos, pos + 2);
    if (["==", "!=", ">=", "<=", "::"].includes(two)) {
      push(two, two, pos);
      pos += 2;
      continue;
    }
    if ("+-*/%><()[]{},:.=@".includes(ch)) {
      push(ch, ch, pos);
      pos++;
      continue;
    }
    fail(pos, `Unexpected character '${ch}'.`);
  }
  push("EOF", null, code.length);
  return tokens;
}

class Parser {
  constructor(code, options) {
    this.tokens = tokenize(code);
    this.pos = 0;
    this.allowBodyless = !!(options && options.allowBodyless);
  }
  current() { return this.tokens[this.pos]; }
  check(...kinds) { return kinds.includes(this.current().type); }
  accept(kind) {
    if (this.current().type === kind) { this.pos++; return true; }
    return false;
  }
  fail(message, token) {
    token = token || this.current();
    throw new KoskriptSyntaxError(message, token.line, token.character);
  }
  expect(kind) {
    if (this.current().type !== kind) this.fail(`Expected ${kind}`);
    this.pos++;
  }
  parse() {
    const stmts = [];
    while (!this.check("EOF")) {
      stmts.push(this.parseStatement());
    }
    return stmts;
  }
  parseStatement() {
    const t = this.current().type;
    if (t === "@") {
      while (this.accept("@")) {
        this.parseDottedName();
        if (this.accept("(")) { this.parseArguments(); this.expect(")"); }
      }
      return this.parseStatement();
    }
    if (t === "LET" || t === "CONST") return this.parseDeclaration();
    if (t === "FUN" || t === "WRAPPER") return this.parseFunction();
    if (t === "CLASS") return this.parseClass();
    if (t === "ERROR") { this.pos++; this.expect("NAME"); this.parseParameters(); this.parseBlock(); return {type:"ErrorDef"}; }
    if (t === "NAMESPACE") { this.pos++; this.expect("NAME"); this.parseBlock(); return {type:"NamespaceDef"}; }
    if (t === "IMPORT") {
      this.pos++;
      this.parseExpression();
      if (this.accept("AS")) this.expect("NAME");
      return {type:"ImportStmt"};
    }
    if (t === "IF") return this.parseIf();
    if (t === "WHILE") return this.parseWhile();
    if (t === "FOR") return this.parseFor();
    if (t === "FOREACH") return this.parseForeach();
    if (t === "RETURN") { this.pos++; if (this.check("EOF") || this.check("}")) return {type:"ReturnStmt"}; this.parseExpression(); return {type:"ReturnStmt"}; }
    if (t === "BREAK") { this.pos++; return {type:"BreakStmt"}; }
    if (t === "THROW") { this.pos++; this.parseExpression(); return {type:"ThrowStmt"}; }
    if (t === "TRY") { this.pos++; this.parseBlock(); if (this.accept("CATCH")) { this.expect("NAME"); this.parseBlock(); } if (this.accept("FINALLY")) this.parseBlock(); return {type:"TryStmt"}; }
    if (t === "CONTINUE") { this.pos++; return {type:"ContinueStmt"}; }
    // expression statement
    this.parseExpression();
    if (this.accept("=")) this.parseExpression();
    return {type:"ExprStmt"};
  }
  parseDeclaration() {
    this.pos++; // let/const
    this.expect("NAME");
    this.expect("=");
    this.parseExpression();
    return {type:"Decl"};
  }
  parseFunction() {
    this.pos++; // fun/wrapper
    this.expect("NAME");
    this.parseParameters();
    if (this.check("{")) this.parseBlock();
    else if (!this.allowBodyless) this.fail("Expected {");
    return {type:"FnDef"};
  }
  parseParameters() {
    this.expect("(");
    if (!this.check(")")) {
      this.expect("NAME");
      while (this.accept(",")) this.expect("NAME");
    }
    this.expect(")");
  }
  parseClass() {
    this.pos++; // class
    this.expect("NAME");
    if (this.accept("EXTENDS")) this.parseDottedName();
    this.expect("{");
    while (!this.check("}") && !this.check("EOF")) {
      // decorators can precede methods, e.g. `@loud public fun ping()`
      while (this.accept("@")) {
        this.parseDottedName();
        if (this.accept("(")) { this.parseArguments(); this.expect(")"); }
      }
      // modifiers
      while (this.check("STATIC") || this.check("PUBLIC") || this.check("PRIVATE")) this.pos++;
      if (this.check("FUN") || this.check("WRAPPER")) this.parseFunction();
      else if (this.check("CONSTRUCTOR")) { this.pos++; this.parseParameters(); this.parseBlock(); }
      else {
        // field: NAME [= expr]
        this.expect("NAME");
        if (this.accept("=")) this.parseExpression();
      }
    }
    this.expect("}");
    return {type:"ClassDef"};
  }
  parseBlock() {
    this.expect("{");
    while (!this.check("}") && !this.check("EOF")) this.parseStatement();
    this.expect("}");
  }
  parseIf() {
    this.pos++;
    this.parseCondition();
    this.parseBlock();
    while (this.check("ELSEIF")) { this.pos++; this.parseCondition(); this.parseBlock(); }
    if (this.accept("ELSE")) this.parseBlock();
    return {type:"IfStmt"};
  }
  parseWhile() {
    this.pos++;
    this.parseCondition();
    this.parseBlock();
    return {type:"WhileStmt"};
  }
  parseFor() {
    this.pos++;
    this.expect("(");
    this.expect("NAME");
    this.expect("IN");
    this.parseExpression();
    this.expect(")");
    this.parseBlock();
    return {type:"ForStmt"};
  }
  parseForeach() {
    this.pos++;
    this.expect("(");
    this.expect("NAME");
    this.expect(",");
    this.expect("NAME");
    this.expect("IN");
    this.parseExpression();
    this.expect(")");
    this.parseBlock();
    return {type:"ForStmt"};
  }
  parseCondition() {
    this.expect("(");
    this.parseExpression();
    this.expect(")");
  }
  parseDottedName() {
    this.expect("NAME");
    while (this.accept(".")) this.expect("NAME");
  }
  parseExpression() {
    this.parseOr();
  }
  parseOr() {
    this.parseAnd();
    while (this.accept("OR")) this.parseAnd();
  }
  parseAnd() {
    this.parseNot();
    while (this.accept("AND")) this.parseNot();
  }
  parseNot() {
    if (this.accept("NOT")) this.parseNot();
    else this.parseComparison();
  }
  parseComparison() {
    this.parseSum();
    if (["==","!=" ,">=", "<=", ">", "<"].includes(this.current().type)) {
      this.pos++;
      this.parseSum();
    }
  }
  parseSum() {
    this.parseTerm();
    while (this.current().type === "+" || this.current().type === "-") {
      this.pos++;
      this.parseTerm();
    }
  }
  parseTerm() {
    this.parseUnary();
    while (["*","/","%"].includes(this.current().type)) {
      this.pos++;
      this.parseUnary();
    }
  }
  parseUnary() {
    if (this.current().type === "-") { this.pos++; this.parseUnary(); return; }
    this.parsePostfix();
  }
  parsePostfix() {
    this.parseAtom();
    while (true) {
      const t = this.current().type;
      if (t === ".") { this.pos++; this.expect("NAME"); }
      else if (t === "[") { this.pos++; this.parseExpression(); this.expect("]"); }
      else if (t === "(") { this.pos++; this.parseArguments(); this.expect(")"); }
      else if (t === "::") { this.pos++; this.expect("NAME"); this.expect("("); this.parseArguments(); this.expect(")"); }
      else break;
    }
  }
  parseArguments() {
    if (this.check(")")) return;
    this.parseExpression();
    while (this.accept(",")) {
      if (this.check(")")) break;
      this.parseExpression();
    }
  }
  parseAtom() {
    const t = this.current().type;
    if (["NUMBER","STRING","NAME"].includes(t)) { this.pos++; return; }
    if (t === "[") { this.pos++; this.parseArray(); return; }
    if (t === "{") { this.pos++; this.parseMap(); return; }
    if (t === "(") {
      this.pos++;
      if (this.accept(")")) {
        // lambda with no params
        if (this.check("{")) this.parseBlock();
        return;
      }
      this.parseExpression();
      while (this.accept(",")) this.parseExpression();
      this.expect(")");
      if (this.check("{")) this.parseBlock();
      return;
    }
    if (t === "NEW") {
      this.pos++;
      this.parseDottedName();
      this.expect("(");
      this.parseArguments();
      this.expect(")");
      return;
    }
    if (["TRUE","FALSE","NULL","THIS","SUPER"].includes(t)) {
      this.pos++;
      if (t==="SUPER") {
        this.expect("::");
        if (this.check("CONSTRUCTOR")) this.pos++; else this.expect("NAME");
        this.expect("("); this.parseArguments(); this.expect(")");
      }
      return;
    }
    if (t === "::") { this.pos++; this.expect("NAME"); this.expect("("); this.parseArguments(); this.expect(")"); return; }
    if (t === ".") { this.pos++; this.expect("NAME"); return; }
    this.fail("Unexpected token " + t);
  }
  parseArray() {
    if (!this.check("]")) {
      this.parseExpression();
      while (this.accept(",")) {
        if (this.check("]")) break;
        this.parseExpression();
      }
    }
    this.expect("]");
  }
  parseMap() {
    if (!this.check("}")) {
      this.parseMapEntry();
      while (this.accept(",")) {
        if (this.check("}")) break;
        this.parseMapEntry();
      }
    }
    this.expect("}");
  }
  parseMapEntry() {
    const t = this.current().type;
    if (t === "[") {
      this.pos++; this.parseExpression(); this.expect("]");
    } else if (t === "NAME" || t === "STRING") {
      this.pos++;
    } else {
      this.fail("Expected map key");
    }
    this.expect("=");
    this.parseExpression();
  }
}

function parse(code, options) {
  const p = new Parser(code, options);
  return p.parse();
}

// SYMBOLS ####################################################################

function emptySymbols() {
  return {
    functions: [],
    classes: [],
    constants: [],
    members: {},            // ClassName -> [{ name, kind }]
    parents: {},            // ClassName -> parent ClassName
    namespaceMembers: {},   // namespace/import alias -> symbol object
    instantiations: {},     // variable -> ClassName
    declarations: [],       // top-level declarations with positions
  };
}

function pushUnique(list, value) {
  if (!list.includes(value)) list.push(value);
}

function addMember(list, name, kind) {
  if (!list || name === "fun" || name === "constructor") return;
  if (!list.some(m => m.name === name)) list.push({ name, kind });
}

function declarationOf(token, kind) {
  return { name: token.value, kind, line: token.line, character: token.character };
}

function skipParens(tokens, openIndex) {
  let depth = 0;
  for (let i = openIndex; i < tokens.length; i++) {
    if (tokens[i].type === "(") depth++;
    else if (tokens[i].type === ")") {
      depth--;
      if (depth === 0) return i + 1;
    }
  }
  return tokens.length - 1;
}

function unquoteLiteral(raw) {
  if (raw.length >= 2) {
    const quote = raw[0];
    if ((quote === '"' || quote === "'") && raw[raw.length - 1] === quote) {
      const escapes = { n: "\n", t: "\t", r: "\r", "0": "\0", "\\": "\\", '"': '"', "'": "'" };
      return raw.slice(1, -1).replace(/\\(.)/g, (m, ch) => Object.prototype.hasOwnProperty.call(escapes, ch) ? escapes[ch] : ch);
    }
  }
  return raw;
}

function resolveImport(rel, baseDir) {
  if (!baseDir) return null;
  let full = path.isAbsolute(rel) ? rel : path.join(baseDir, rel);
  if (!fs.existsSync(full)) {
    if (fs.existsSync(full + ".kosh")) full += ".kosh";
    else if (fs.existsSync(full + ".kos")) full += ".kos";
  }
  return fs.existsSync(full) ? full : null;
}

function mergeSymbols(target, source) {
  for (const f of source.functions) pushUnique(target.functions, f);
  for (const c of source.classes) pushUnique(target.classes, c);
  for (const v of source.constants) pushUnique(target.constants, v);
  for (const [k, v] of Object.entries(source.members || {})) {
    if (!target.members[k]) target.members[k] = v;
  }
  for (const [k, v] of Object.entries(source.parents || {})) {
    if (!target.parents[k]) target.parents[k] = v;
  }
  for (const [k, v] of Object.entries(source.namespaceMembers || {})) {
    if (!target.namespaceMembers[k]) target.namespaceMembers[k] = v;
  }
  for (const [k, v] of Object.entries(source.instantiations || {})) {
    target.instantiations[k] = v;
  }
}

function collectSymbols(code, baseDir, seen, resolve) {
  const syms = emptySymbols();
  seen = seen || new Set();
  // `resolve(specifier, fromDir)` lets the server look imports up in the
  // project-wide header index; without it imports are relative to `baseDir`.
  const resolveImportPath = resolve || resolveImport;

  let tokens;
  try {
    tokens = tokenize(code);
  } catch (e) {
    return syms;
  }

  // Context stack: global/namespace/class/function/block. Declarations are
  // recorded only when their immediate container is global, a namespace or a
  // class, so names inside functions, control-flow blocks and map literals do
  // not leak into the global completion surface.
  const stack = [{ kind: "global", syms }];
  const current = () => stack[stack.length - 1];

  for (let i = 0; i < tokens.length; i++) {
    const t = tokens[i];
    if (t.type === "EOF") break;

    if (t.type === "NAMESPACE") {
      const nameTok = tokens[i + 1];
      let j = i + 1;
      if (nameTok && nameTok.type === "NAME") j++;
      while (tokens[j] && tokens[j].type !== "{" && tokens[j].type !== "EOF") j++;
      if (tokens[j] && tokens[j].type === "{") {
        const inner = emptySymbols();
        const container = current();
        if ((container.kind === "global" || container.kind === "namespace") && nameTok && nameTok.type === "NAME") {
          if (!container.syms.namespaceMembers[nameTok.value]) {
            container.syms.namespaceMembers[nameTok.value] = inner;
          }
          if (container.kind === "global") {
            container.syms.declarations.push(declarationOf(nameTok, "namespace"));
          }
        }
        stack.push({ kind: "namespace", syms: inner });
        i = j;
        continue;
      }
      continue;
    }

    if (t.type === "CLASS") {
      const nameTok = tokens[i + 1];
      if (!nameTok || nameTok.type !== "NAME") continue;
      let j = i + 2;
      let parent = null;
      if (tokens[j] && tokens[j].type === "EXTENDS") {
        j++;
        while (tokens[j] && (tokens[j].type === "NAME" || tokens[j].type === ".")) {
          if (tokens[j].type === "NAME") parent = tokens[j].value;
          j++;
        }
      }
      while (tokens[j] && tokens[j].type !== "{" && tokens[j].type !== "EOF") j++;
      if (tokens[j] && tokens[j].type === "{") {
        const container = current();
        const record = container.kind === "global" || container.kind === "namespace";
        if (record) {
          container.syms.classes.push(nameTok.value);
          if (container.kind === "global") {
            container.syms.declarations.push(declarationOf(nameTok, "class"));
          }
        }
        if (record && !syms.members[nameTok.value]) syms.members[nameTok.value] = [];
        if (record) syms.parents[nameTok.value] = parent;
        stack.push({ kind: "class", className: nameTok.value, record });
        i = j;
        continue;
      }
      continue;
    }

    if (t.type === "FUN" || t.type === "WRAPPER" || t.type === "ERROR" || t.type === "CONSTRUCTOR") {
      let j = i + 1;
      let nameTok = null;
      if (t.type !== "CONSTRUCTOR") {
        nameTok = tokens[j];
        if (nameTok && nameTok.type === "NAME") j++;
        else nameTok = null;
      }
      if (tokens[j] && tokens[j].type === "(") j = skipParens(tokens, j);

      const container = current();
      if (nameTok) {
        if (t.type === "FUN" || t.type === "WRAPPER") {
          if (container.kind === "class") {
            if (container.record) addMember(syms.members[container.className], nameTok.value, "method");
          } else if (container.kind === "global" || container.kind === "namespace") {
            container.syms.functions.push(nameTok.value);
            if (container.kind === "global") {
              container.syms.declarations.push(declarationOf(nameTok, "function"));
            }
          }
        } else if (t.type === "ERROR" && (container.kind === "global" || container.kind === "namespace")) {
          container.syms.functions.push(nameTok.value);
          if (container.kind === "global") {
            container.syms.declarations.push(declarationOf(nameTok, "error"));
          }
        }
      }

      if (tokens[j] && tokens[j].type === "{") {
        stack.push({ kind: "function" });
        i = j;
        continue;
      }
      i = j - 1;
      continue;
    }

    if (t.type === "@") {
      // `@decorator` or `@decorator(args)`; skip it so the following method
      // is still recognised as a class member.
      let j = i + 1;
      if (tokens[j] && tokens[j].type === "NAME") {
        j++;
        while (tokens[j] && tokens[j].type === "." && tokens[j + 1] && tokens[j + 1].type === "NAME") j += 2;
        if (tokens[j] && tokens[j].type === "(") j = skipParens(tokens, j);
      }
      i = j - 1;
      continue;
    }

    if (t.type === "IMPORT") {
      const pathTok = tokens[i + 1];
      if (pathTok && pathTok.type === "STRING") {
        let j = i + 2;
        let alias = null;
        if (tokens[j] && tokens[j].type === "AS" && tokens[j + 1] && tokens[j + 1].type === "NAME") {
          alias = tokens[j + 1].value;
          j += 2;
        }
        const full = resolveImportPath(unquoteLiteral(pathTok.value), baseDir);
        if (full && !seen.has(full)) {
          seen.add(full);
          try {
            const imported = fs.readFileSync(full, "utf8");
            const isyms = collectSymbols(imported, path.dirname(full), seen, resolveImportPath);
            const container = current();
            const target = (container.kind === "global" || container.kind === "namespace") ? container.syms : syms;
            const aliasName = alias || path.basename(full).replace(/\.(kosh|kos|koskript)$/i, "");
            if (target.namespaceMembers[aliasName]) mergeSymbols(target.namespaceMembers[aliasName], isyms);
            else target.namespaceMembers[aliasName] = isyms;
            for (const f of isyms.functions) pushUnique(target.functions, aliasName + "." + f);
            for (const c of isyms.classes) pushUnique(target.classes, aliasName + "." + c);
            for (const v of isyms.constants) pushUnique(target.constants, aliasName + "." + v);
            // Instance/class data is global to the document, so a variable
            // created from an imported class can still resolve its members.
            for (const [k, v] of Object.entries(isyms.members)) {
              if (!syms.members[k]) syms.members[k] = v;
            }
            for (const [k, v] of Object.entries(isyms.parents)) {
              if (!syms.parents[k]) syms.parents[k] = v;
            }
            for (const [k, v] of Object.entries(isyms.instantiations)) {
              syms.instantiations[k] = v;
            }
          } catch (e) {}
        }
        i = j - 1;
        continue;
      }
    }

    if (t.type === "LET" || t.type === "CONST") {
      const nameTok = tokens[i + 1];
      const eq = tokens[i + 2];
      const nw = tokens[i + 3];
      if (nameTok && nameTok.type === "NAME" && eq && eq.type === "=" && nw && nw.type === "NEW") {
        let j = i + 4;
        let last = null;
        while (tokens[j] && tokens[j].type === "NAME") {
          last = tokens[j].value;
          if (tokens[j + 1] && tokens[j + 1].type === ".") { j += 2; continue; }
          break;
        }
        if (last) syms.instantiations[nameTok.value] = last;
      }
      if (t.type === "CONST" && nameTok && nameTok.type === "NAME") {
        const container = current();
        if (container.kind === "global" || container.kind === "namespace") {
          container.syms.constants.push(nameTok.value);
          if (container.kind === "global") {
            container.syms.declarations.push(declarationOf(nameTok, "constant"));
          }
        }
      }
      continue;
    }

    if (t.type === "STATIC" || t.type === "PUBLIC" || t.type === "PRIVATE") continue;

    if (t.type === "NAME") {
      const container = current();
      if (container.kind === "class" && container.record && tokens[i + 1] && tokens[i + 1].type === "=") {
        addMember(syms.members[container.className], t.value, "field");
        continue;
      }
      continue;
    }

    if (t.type === "{") {
      stack.push({ kind: "block" });
      continue;
    }
    if (t.type === "}") {
      if (stack.length > 1) stack.pop();
      continue;
    }
  }

  return syms;
}

function enclosingClass(code, offset) {
  let tokens;
  try {
    tokens = tokenize(code);
  } catch (e) {
    return null;
  }
  const stack = [];
  for (let i = 0; i < tokens.length; i++) {
    const t = tokens[i];
    if (t.type === "EOF" || t.offset > offset) break;
    if (t.type === "CLASS") {
      const nameTok = tokens[i + 1];
      if (!nameTok || nameTok.type !== "NAME") continue;
      let j = i + 2;
      while (tokens[j] && tokens[j].type !== "{" && tokens[j].type !== "EOF") j++;
      if (tokens[j] && tokens[j].type === "{") {
        stack.push({ kind: "class", name: nameTok.value });
        i = j;
        continue;
      }
      continue;
    }
    if (t.type === "{") stack.push({ kind: "block" });
    else if (t.type === "}") stack.pop();
  }
  for (let k = stack.length - 1; k >= 0; k--) {
    if (stack[k].kind === "class") return stack[k].name;
  }
  return null;
}

module.exports = {
  parse,
  tokenize,
  collectSymbols,
  enclosingClass,
  KoskriptSyntaxError,
};
