// Project-wide index of Koskript header files (`.kosh`).
//
// Headers are not tied to one folder: a project can keep them at its root, next
// to the scripts that use them or inside a `modules/` directory, and every
// script in the project should still complete their declarations. This module
// scans the workspace once, caches the parsed symbols and resolves imports
// against both the filesystem and the index.
const fs = require("fs");
const path = require("path");
const { collectSymbols } = require("./parser");

const IGNORED_DIRS = new Set([
  "node_modules", ".git", ".hg", ".svn", ".venv", "venv", "env",
  "__pycache__", ".pytest_cache", ".mypy_cache", ".tox", ".ruff_cache",
  "dist", "build", "out", "target", "bin", "obj", "coverage", "site-packages",
  ".vscode", ".idea", ".next", ".nuxt", ".cache", ".gradle", ".cargo",
]);

const PROJECT_MARKERS = [
  ".git", "pyproject.toml", "package.json", "koskript.toml", "koskript.json",
];

const MAX_DEPTH = 12;
const MAX_FILES = 5000;
const CACHE_MS = 1500;
const EXTENSIONS = [".kosh", ".kos"];
const MODULE_RE = /^[A-Za-z_][A-Za-z0-9_]*$/;

function isKosh(name) {
  return name.toLowerCase().endsWith(".kosh");
}

function hashText(text) {
  // FNV-1a, enough to notice edits of an open header between completions.
  let hash = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return hash.toString(16) + ":" + text.length;
}

function statSignature(file) {
  try {
    const st = fs.statSync(file);
    return `${st.mtimeMs}:${st.size}`;
  } catch (e) {
    return null;
  }
}

function normalizeSpec(spec) {
  return String(spec)
    .replace(/\\/g, "/")
    .replace(/^\.\//, "")
    .replace(/\.(kosh|kos|koskript)$/i, "");
}

function existingFile(file) {
  if (!file) return null;
  try {
    if (fs.statSync(file).isFile()) return file;
  } catch (e) { /* keep looking */ }
  for (const ext of EXTENSIONS) {
    try {
      if (fs.statSync(file + ext).isFile()) return file + ext;
    } catch (e) { /* keep looking */ }
  }
  return null;
}

function isInside(child, parent) {
  const rel = path.relative(parent, child);
  return rel === "" || (!rel.startsWith("..") && !path.isAbsolute(rel));
}

function depthOf(fromDir, toDir) {
  if (!fromDir) return 0;
  const rel = path.relative(fromDir, toDir);
  if (!rel) return 0;
  return rel.split(path.sep).filter(Boolean).length;
}

// Nearest ancestor (including `dir`) that looks like a project root: it has a
// `.kosh` file, a VCS marker or a manifest. Used when no workspace is open.
function projectRootOf(dir) {
  let current = path.resolve(dir);
  let found = null;
  for (let i = 0; i < 10; i++) {
    let has = false;
    try {
      const entries = fs.readdirSync(current, { withFileTypes: true });
      has = entries.some(e => isKosh(e.name) || PROJECT_MARKERS.includes(e.name));
    } catch (e) {
      break;
    }
    if (has) found = current;
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return found;
}

class HeaderIndex {
  constructor() {
    this.roots = [];
    this.extraRoots = [];
    this.files = new Map();
    this.lastScan = 0;
    this.getText = () => null;
  }

  /** Workspace folders, as absolute paths. */
  setRoots(roots) {
    this.roots = (roots || []).filter(Boolean).map(r => path.resolve(r));
    this.extraRoots = this.extraRoots.filter(r => !this.roots.includes(r));
    this.lastScan = 0;
    this.refresh(true);
  }

  /** Called with an absolute path to read an open (possibly unsaved) document. */
  setTextProvider(fn) {
    this.getText = typeof fn === "function" ? fn : () => null;
  }

  /** Drop the cache so the next lookup re-stats every header. */
  invalidate() {
    this.lastScan = 0;
  }

  allRoots() {
    return this.roots.concat(this.extraRoots);
  }

  refresh(force) {
    const now = Date.now();
    if (!force && now - this.lastScan < CACHE_MS) return;
    this.lastScan = now;
    const next = new Map();
    for (const root of this.allRoots()) this._walk(root, root, 0, next);
    this.files = next;
  }

  _walk(dir, root, depth, out) {
    if (depth > MAX_DEPTH || out.size >= MAX_FILES) return;
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch (e) {
      return;
    }
    for (const entry of entries) {
      if (out.size >= MAX_FILES) return;
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name.startsWith(".") || IGNORED_DIRS.has(entry.name.toLowerCase())) continue;
        this._walk(full, root, depth + 1, out);
      } else if (entry.isFile() && isKosh(entry.name)) {
        const record = this._record(full, root);
        if (record) out.set(full, record);
      }
    }
  }

  _record(full, root) {
    const dir = path.dirname(full);
    const openText = this.getText(full);
    const signature = openText == null ? statSignature(full) : "open:" + hashText(openText);
    const cached = this.files.get(full);
    if (cached && cached.signature === signature && cached.root === root) return cached;

    let code = openText;
    if (code == null) {
      try {
        code = fs.readFileSync(full, "utf8");
      } catch (e) {
        return null;
      }
    }

    let symbols;
    try {
      symbols = collectSymbols(code, dir);
    } catch (e) {
      return null;
    }

    return {
      path: full,
      dir,
      root,
      relPath: path.relative(root, full).replace(/\\/g, "/"),
      moduleName: path.basename(full).replace(/\.kosh$/i, ""),
      symbols,
      signature,
    };
  }

  /** Deepest root that contains `docPath`, if any. */
  rootFor(docPath) {
    let best = null;
    for (const root of this.allRoots()) {
      if (!isInside(docPath, root)) continue;
      if (!best || root.length > best.length) best = root;
    }
    return best;
  }

  /**
   * Headers visible from a document, nearest first. When the document is not
   * inside a workspace folder, its project root is discovered by walking up.
   */
  entriesFor(docPath) {
    this.refresh();
    let root = this.rootFor(docPath);
    if (!root) {
      const guessed = projectRootOf(path.dirname(docPath));
      if (guessed && !this.extraRoots.includes(guessed)) {
        this.extraRoots.push(guessed);
        this.refresh(true);
        root = guessed;
      }
    }

    const dir = path.dirname(docPath);
    const list = [];
    for (const entry of this.files.values()) {
      if (root && entry.root !== root) continue;
      if (!root && !isInside(entry.path, dir)) continue;
      list.push(entry);
    }
    list.sort((a, b) =>
      depthOf(dir, a.dir) - depthOf(dir, b.dir) ||
      a.relPath.length - b.relPath.length ||
      a.relPath.localeCompare(b.relPath)
    );
    return list;
  }

  /**
   * Import resolver used by `collectSymbols`: relative to the importing file,
   * then relative to the project root, then any indexed header whose path or
   * module name matches.
   */
  resolverFor(docPath) {
    const docDir = path.dirname(docPath);
    const roots = this.allRoots().filter(r => isInside(docPath, r));
    return (spec, fromDir) => {
      if (!spec) return null;
      const base = fromDir || docDir;
      if (path.isAbsolute(spec)) return existingFile(spec);

      const direct = existingFile(path.join(base, spec));
      if (direct) return direct;

      for (const root of roots) {
        const found = existingFile(path.join(root, spec));
        if (found) return found;
      }

      return this.findModule(spec, base);
    };
  }

  /** Best indexed header for a module specifier such as `utils` or `lib/utils`. */
  findModule(spec, fromDir) {
    this.refresh();
    const wanted = normalizeSpec(spec);
    if (!wanted) return null;

    let best = null;
    let bestScore = Infinity;
    for (const entry of this.files.values()) {
      const rel = entry.relPath.replace(/\.kosh$/i, "");
      const matches = rel === wanted || rel.endsWith("/" + wanted) || entry.moduleName === wanted;
      if (!matches) continue;
      const score = depthOf(fromDir, entry.dir) * 1000 + rel.length;
      if (score < bestScore) {
        bestScore = score;
        best = entry;
      }
    }
    return best ? best.path : null;
  }
}

module.exports = {
  HeaderIndex,
  IGNORED_DIRS,
  MODULE_RE,
  isKosh,
  normalizeSpec,
  projectRootOf,
};
