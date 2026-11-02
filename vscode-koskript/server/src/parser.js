const fs = require("fs");
const path = require("path");
const RESERVED = new Set([
  "if","elseif","else","while","for","foreach","fun","wrapper","return","let","const",
  "true","false","null","and","or","not","in","break","continue","class","extends","new",
  "static","public","private","this","super","constructor","import","as","error","throw",
  "try","catch","finally","namespace"
]);

function tokenize(code) {
  const tokens = [];
  let pos = 0;
  const len = code.length;
  while (pos < len) {
    const ch = code[pos];
    if (/\s/.test(ch)) { pos++; continue; }
    if (ch === "/" && code[pos+1] === "/") {
      while (pos < len && code[pos] !== "\n") pos++;
      continue;
    }
    if (/[0-9]/.test(ch)) {
      let start = pos;
      while (pos < len && /[0-9]/.test(code[pos])) pos++;
      if (code[pos] === "." && /[0-9]/.test(code[pos+1])) {
        pos++;
        while (pos < len && /[0-9]/.test(code[pos])) pos++;
      }
      tokens.push({ type: "NUMBER", value: code.slice(start, pos) });
      continue;
    }
    if (ch === '"' || ch === "'") {
      const quote = ch;
      let start = pos;
      pos++;
      while (pos < len && code[pos] !== quote) {
        if (code[pos] === "\\") pos++;
        pos++;
      }
      if (pos >= len) throw new Error("Unterminated string");
      pos++;
      tokens.push({ type: "STRING", value: code.slice(start, pos) });
      continue;
    }
    if (/[a-zA-Z_]/.test(ch)) {
      let start = pos;
      while (pos < len && /[a-zA-Z0-9_]/.test(code[pos])) pos++;
      const word = code.slice(start, pos);
      if (RESERVED.has(word)) tokens.push({ type: word.toUpperCase(), value: word });
      else tokens.push({ type: "NAME", value: word });
      continue;
    }
    // two-char operators
    const two = code.slice(pos, pos+2);
    if (["==","!=",">=","<=","::"].includes(two)) {
      tokens.push({ type: two, value: two });
      pos += 2;
      continue;
    }
    if ("+-*/%><()[]{},:.=@".includes(ch)) {
      tokens.push({ type: ch, value: ch });
      pos++;
      continue;
    }
    throw new Error(`Unexpected character ${ch}`);
  }
  tokens.push({ type: "EOF", value: null });
  return tokens;
}

class Parser {
  constructor(code) {
    this.tokens = tokenize(code);
    this.pos = 0;
  }
  current() { return this.tokens[this.pos]; }
  check(...kinds) { return kinds.includes(this.current().type); }
  accept(kind) {
    if (this.current().type === kind) { this.pos++; return true; }
    return false;
  }
  expect(kind) {
    if (this.current().type !== kind) throw new Error(`Expected ${kind}`);
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
    if (t === "@") { while (this.accept("@")) { this.parseDottedName(); if (this.accept("(")) { this.parseArguments(); this.expect(")"); } } return this.parseStatement(); }
    if (t === "LET" || t === "CONST") return this.parseDeclaration();
    if (t === "FUN" || t === "WRAPPER") return this.parseFunction();
    if (t === "CLASS") return this.parseClass();
    if (t === "ERROR") { this.pos++; this.expect("NAME"); this.parseParameters(); this.parseBlock(); return {type:"ErrorDef"}; }
    if (t === "NAMESPACE") { this.pos++; this.expect("NAME"); this.parseBlock(); return {type:"NamespaceDef"}; }
    if (t === "IMPORT") { this.pos++; this.parseExpression(); if (this.accept("AS")) this.expect("NAME"); return {type:"ImportStmt"}; }
    if (t === "IMPORT") { this.pos++; this.parseExpression(); return {type:"ImportStmt"}; }
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
    throw new Error("Unexpected token " + t);
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
      throw new Error("Expected map key");
    }
    this.expect("=");
    this.parseExpression();
  }
}

function parse(code) {
  const p = new Parser(code);
  try { return p.parse(); }
  catch (e) {
    throw new Error(e.message);
  }
}

function collectSymbols(code, baseDir) {
  const syms = {
    functions: [],
    classes: [],
    constants: [],
    members: {},            // ClassName -> [{ name, kind }]
    parents: {},            // ClassName -> parent ClassName
    namespaceMembers: {},   // namespace/import alias -> symbol object
    instantiations: {},     // variable -> ClassName
  };

  // namespace -> member list
  const nsRe = /\bnamespace\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{/g;
  let nsm;
  while ((nsm = nsRe.exec(code)) !== null) {
    let depth = 1;
    let i = nsm.index + nsm[0].length;
    while (i < code.length && depth > 0) {
      if (code[i] === "{") depth++;
      else if (code[i] === "}") depth--;
      i++;
    }
    const body = code.slice(nsm.index + nsm[0].length, i - 1);
    const inner = collectSymbols(body, baseDir);
    syms.namespaceMembers[nsm[1]] = inner;
  }

  // objects: `let x = new Class(...)`
  const objRe = /\b(?:let|const)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*new\s+([A-Za-z_.][A-Za-z0-9_.]*)/g;
  let om;
  while ((om = objRe.exec(code)) !== null) {
    const className = om[2].split(".").pop();
    syms.instantiations[om[1]] = className;
  }

  // class members (methods and fields)
  const clsRe = /\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:(?:extends\s+[A-Za-z_][A-Za-z0-9_.]+)\s*)?\{/g;
  let cm;
  while ((cm = clsRe.exec(code)) !== null) {
    const start = cm.index + cm[0].length;
    let depth = 1;
    let i = start;
    while (i < code.length && depth > 0) {
      if (code[i] === "{") depth++;
      else if (code[i] === "}") depth--;
      i++;
    }
    const body = code.slice(start, i - 1);
    const members = [];
    const seen = new Set();
    const addMember = (name, kind) => {
      if (name === "fun" || seen.has(name)) return;
      seen.add(name);
      members.push({ name, kind });
    };
    const methodRe = /\b(?:public|private|static)\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(|\bfun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(/g;
    let mm;
    while ((mm = methodRe.exec(body)) !== null) addMember(mm[1] || mm[2], "method");
    const fieldRe = /\b(?:public|private|static)\s+(?!fun\b)(?:let\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|$)/g;
    while ((mm = fieldRe.exec(body)) !== null) addMember(mm[1], "field");
    syms.members[cm[1]] = members;

    const extMatch = /extends\s+([A-Za-z_][A-Za-z0-9_.]+)/.exec(cm[0]);
    syms.parents[cm[1]] = extMatch ? extMatch[1].split(".").pop() : null;
  }

  const fnRe = /\bfun\s+([A-Za-z_][A-Za-z0-9_]*)/g;
  let m;
  while ((m = fnRe.exec(code)) !== null) syms.functions.push(m[1]);
  const classRe = /\bclass\s+([A-Za-z_][A-Za-z0-9_]*)/g;
  while ((m = classRe.exec(code)) !== null) syms.classes.push(m[1]);
  const constRe = /\bconst\s+([A-Za-z_][A-Za-z0-9_]*)/g;
  while ((m = constRe.exec(code)) !== null) syms.constants.push(m[1]);

  const importRe = /\bimport\s+"([^"]+)"(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?/g;
  let im;
  while ((im = importRe.exec(code)) !== null) {
    const rel = im[1];
    const alias = im[2];
    if (!baseDir) continue;
    let full = path.isAbsolute(rel) ? rel : path.join(baseDir, rel);
    if (!fs.existsSync(full)) {
      if (fs.existsSync(full + ".kosh")) full += ".kosh";
      else if (fs.existsSync(full + ".kos")) full += ".kos";
    }
    if (!fs.existsSync(full)) continue;
    try {
      const imported = fs.readFileSync(full, "utf8");
      const isyms = collectSymbols(imported, path.dirname(full));
      const aliasName = alias || path.basename(full).replace(/\.(kosh|kos|koskript)$/i, "");
      if (!syms.namespaceMembers[aliasName]) syms.namespaceMembers[aliasName] = isyms;
      else {
        const tgt = syms.namespaceMembers[aliasName];
        const mergeSyms = (arr) => { for (const x of arr) if (!tgt.includes(x)) tgt.push(x); };
        mergeSyms(isyms.functions); mergeSyms(isyms.classes); mergeSyms(isyms.constants);
        for (const [k, v] of Object.entries(isyms.members || {})) {
          const t2 = tgt.members = tgt.members || {};
          if (!t2[k]) t2[k] = v;
        }
        for (const [k, v] of Object.entries(isyms.namespaceMembers || {})) {
          const t3 = tgt.namespaceMembers = tgt.namespaceMembers || {};
          if (!t3[k]) t3[k] = v;
        }
        for (const [k, v] of Object.entries(isyms.instantiations || {})) {
          const t4 = tgt.instantiations = tgt.instantiations || {};
          t4[k] = v;
        }
      }
      syms.namespaceMembers[aliasName].__path = full;
      const prefix = (alias || aliasName) + ".";
      for (const f of isyms.functions) syms.functions.push(prefix + f);
      for (const c of isyms.classes) syms.classes.push(prefix + c);
      for (const v of isyms.constants) syms.constants.push(prefix + v);
    } catch (e) {}
  }
  return syms;
}

module.exports = { parse, collectSymbols };