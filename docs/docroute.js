(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.docroute = factory();
})(typeof globalThis !== "undefined" ? globalThis : typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var VERSION = "1.0.0";
  var MARKED_URL = "https://cdn.jsdelivr.net/npm/marked@12/marked.min.js";
  var HIGHLIGHT_URL = "https://cdn.jsdelivr.net/npm/@highlightjs/cdn-assets@11/highlight.min.js";
  var THEME_KEY = "docroute-theme";
  var FALLBACK_CSS = `.docroute {
  --d-radius: 12px;
  --d-bg: #0a0a0b;
  --d-panel: #101013;
  --d-panel-2: #17171b;
  --d-border: #232329;
  --d-text: #ececef;
  --d-muted: #8b8b94;
  --d-primary: #f2f2f4;
  --d-primary-soft: rgba(255, 255, 255, 0.08);
  --d-primary-soft: color-mix(in srgb, var(--d-primary) 14%, transparent);
  --d-code-string: #9ecb8f;
  --d-code-number: #e0a878;
  --d-code-function: #8ab4f8;
  --d-code-tag: #e39aa6;
  --d-font: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --d-mono: ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
  display: flex;
  min-height: 100vh;
  background: var(--d-bg);
  color: var(--d-text);
  font-family: var(--d-font);
  font-size: 15px;
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
}

.docroute[data-docroute-theme="light"] {
  --d-bg: #ffffff;
  --d-panel: #fafafa;
  --d-panel-2: #f2f2f3;
  --d-border: #e4e4e7;
  --d-text: #17171a;
  --d-muted: #6b6b74;
  --d-primary: #17171a;
  --d-primary-soft: rgba(23, 23, 26, 0.07);
  --d-primary-soft: color-mix(in srgb, var(--d-primary) 12%, transparent);
  --d-code-string: #3f7a45;
  --d-code-number: #a35a1f;
  --d-code-function: #2f5fb3;
  --d-code-tag: #a03a48;
}

.docroute *,
.docroute *::before,
.docroute *::after {
  box-sizing: border-box;
}

.docroute ::selection {
  background: var(--d-primary-soft);
  color: var(--d-text);
}

.docroute a {
  color: inherit;
  text-decoration: none;
}

.docroute button {
  font: inherit;
}

.docroute [hidden] {
  display: none !important;
}

.docroute-sidebar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  flex: 0 0 272px;
  flex-direction: column;
  height: 100vh;
  overflow-y: auto;
  background: var(--d-panel);
  border-right: 1px solid var(--d-border);
}

.docroute-sidebar::-webkit-scrollbar {
  width: 10px;
}

.docroute-sidebar::-webkit-scrollbar-thumb {
  background: var(--d-border);
  border: 3px solid var(--d-panel);
  border-radius: 999px;
}

.docroute-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px 18px 10px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
  cursor: pointer;
}

.docroute-brand-mark {
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border-radius: 7px;
  background: var(--d-text);
  color: var(--d-bg);
  font-size: 12px;
  font-weight: 700;
}

.docroute-brand-logo {
  width: 22px;
  height: 22px;
  border-radius: 7px;
  object-fit: contain;
  flex: 0 0 auto;
}

.docroute-brand-name {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.docroute-search {
  padding: 2px 10px 10px;
}

.docroute-search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--d-border);
  border-radius: var(--d-radius);
  background: var(--d-bg);
  color: var(--d-text);
  font-family: inherit;
  font-size: 13.5px;
}

.docroute-search-input::placeholder {
  color: var(--d-muted);
}

.docroute-search-input:focus {
  border-color: var(--d-primary);
  box-shadow: 0 0 0 3px var(--d-primary-soft);
  outline: none;
}

.docroute-search-empty {
  padding: 8px 20px;
  color: var(--d-muted);
  font-size: 13px;
}

.docroute-nav {
  padding: 6px 10px 28px;
}

.docroute-section + .docroute-section {
  margin-top: 20px;
}

.docroute-section-title {
  padding: 6px 10px;
  color: var(--d-muted);
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.docroute-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 3px 0;
  padding: 7px 10px;
  border-radius: var(--d-radius);
  color: var(--d-muted);
  font-size: 14px;
  line-height: 1.45;
}

.docroute-item > span:first-child {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.docroute-item:hover {
  background: var(--d-panel-2);
  color: var(--d-text);
}

.docroute-item.is-active {
  background: var(--d-primary-soft);
  color: var(--d-text);
  font-weight: 500;
}

.docroute-external-glyph {
  margin-left: auto;
  font-size: 12px;
  opacity: 0.65;
}

.docroute-sidebar-footer {
  margin-top: auto;
  padding: 14px 20px 16px;
  border-top: 1px solid var(--d-border);
  color: var(--d-muted);
  font-size: 12px;
}

.docroute-sidebar-footer a {
  color: var(--d-muted);
}

.docroute-sidebar-footer a:hover {
  color: var(--d-text);
}

.docroute-overlay {
  display: none;
}

.docroute-main {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  min-width: 0;
}

.docroute-topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 12px;
  height: 56px;
  padding: 0 20px;
  background: var(--d-bg);
  background: color-mix(in srgb, var(--d-bg) 82%, transparent);
  border-bottom: 1px solid var(--d-border);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.docroute-crumbs {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: var(--d-muted);
  font-size: 13px;
}

.docroute-crumb-sep {
  opacity: 0.5;
}

.docroute-crumb-current {
  overflow: hidden;
  color: var(--d-text);
  font-weight: 500;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.docroute-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.docroute-icon-btn {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border: 1px solid var(--d-border);
  border-radius: var(--d-radius);
  background: var(--d-panel);
  color: var(--d-text);
  font-size: 15px;
  cursor: pointer;
}

.docroute-icon-btn:hover {
  background: var(--d-panel-2);
}

.docroute-menu-btn {
  display: none;
}

.docroute-content {
  flex: 1 0 auto;
  width: 100%;
  max-width: 860px;
  margin: 0 auto;
  padding: 40px 28px 96px;
}

.docroute-content > *:first-child {
  margin-top: 0;
}

.docroute-content h1,
.docroute-content h2,
.docroute-content h3,
.docroute-content h4,
.docroute-content h5,
.docroute-content h6 {
  margin: 36px 0 12px;
  line-height: 1.25;
  letter-spacing: -0.02em;
}

.docroute-content h1 {
  margin-top: 0;
  font-size: 2rem;
}

.docroute-content h2 {
  padding-bottom: 8px;
  border-bottom: 1px solid var(--d-border);
  font-size: 1.35rem;
}

.docroute-content h3 {
  font-size: 1.12rem;
}

.docroute-content h4 {
  font-size: 1rem;
}

.docroute-content p,
.docroute-content ul,
.docroute-content ol,
.docroute-content .docroute-table-wrap,
.docroute-content pre,
.docroute-content blockquote,
.docroute-content details {
  margin: 0 0 16px;
}

.docroute-content ul,
.docroute-content ol {
  padding-left: 24px;
}

.docroute-content li + li {
  margin-top: 4px;
}

.docroute-content li:has(> input[type="checkbox"]) {
  list-style: none;
  margin-left: -1.4em;
}

.docroute-content input[type="checkbox"] {
  margin-right: 8px;
  vertical-align: middle;
}

.docroute-content a {
  color: var(--d-primary);
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 3px;
}

.docroute-content a:hover {
  text-decoration-thickness: 2px;
}

.docroute-content strong {
  color: var(--d-text);
  font-weight: 600;
}

.docroute-content code {
  padding: 2px 6px;
  border: 1px solid var(--d-border);
  border-radius: 7px;
  background: var(--d-panel-2);
  font-family: var(--d-mono);
  font-size: 0.85em;
}

.docroute-content pre {
  overflow: auto;
  padding: 14px 16px;
  border: 1px solid var(--d-border);
  border-radius: var(--d-radius);
  background: var(--d-panel);
}

.docroute-content pre code {
  padding: 0;
  border: 0;
  border-radius: 0;
  background: none;
  font-size: 13px;
  line-height: 1.6;
}

.docroute-code {
  position: relative;
  margin: 0 0 16px;
}

.docroute-code pre {
  margin: 0;
}

.docroute-copy-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 4px 10px;
  border: 1px solid var(--d-border);
  border-radius: var(--d-radius);
  background: var(--d-panel-2);
  color: var(--d-muted);
  font-family: inherit;
  font-size: 11.5px;
  line-height: 1.45;
  cursor: pointer;
}

.docroute-copy-btn:hover {
  border-color: var(--d-primary);
  color: var(--d-text);
}

.docroute-copy-btn.is-copied {
  border-color: var(--d-primary);
  color: var(--d-primary);
}

.docroute-content .hljs-comment,
.docroute-content .hljs-quote {
  color: var(--d-muted);
  font-style: italic;
}

.docroute-content .hljs-keyword,
.docroute-content .hljs-selector-tag,
.docroute-content .hljs-literal,
.docroute-content .hljs-section,
.docroute-content .hljs-doctag,
.docroute-content .hljs-operator {
  color: var(--d-primary);
}

.docroute-content .hljs-string,
.docroute-content .hljs-regexp,
.docroute-content .hljs-char.escape_,
.docroute-content .hljs-subst,
.docroute-content .hljs-symbol,
.docroute-content .hljs-bullet,
.docroute-content .hljs-addition {
  color: var(--d-code-string);
}

.docroute-content .hljs-number,
.docroute-content .hljs-variable,
.docroute-content .hljs-template-variable,
.docroute-content .hljs-attr,
.docroute-content .hljs-attribute,
.docroute-content .hljs-selector-attr,
.docroute-content .hljs-selector-pseudo,
.docroute-content .hljs-property {
  color: var(--d-code-number);
}

.docroute-content .hljs-title,
.docroute-content .hljs-built_in,
.docroute-content .hljs-type,
.docroute-content .hljs-class .hljs-title,
.docroute-content .hljs-function .hljs-title {
  color: var(--d-code-function);
}

.docroute-content .hljs-tag,
.docroute-content .hljs-name,
.docroute-content .hljs-selector-id,
.docroute-content .hljs-selector-class,
.docroute-content .hljs-template-tag,
.docroute-content .hljs-deletion,
.docroute-content .hljs-meta {
  color: var(--d-code-tag);
}

.docroute-content .hljs-emphasis {
  font-style: italic;
}

.docroute-content .hljs-strong {
  font-weight: 600;
}

.docroute-content .hljs-link {
  text-decoration: underline;
}

.docroute-content blockquote {
  margin-left: 0;
  padding: 2px 0 2px 16px;
  border-left: 2px solid var(--d-primary);
  color: var(--d-muted);
}

.docroute-content blockquote > *:last-child {
  margin-bottom: 0;
}

.docroute-callout {
  margin: 0 0 16px;
  padding: 12px 16px;
  border: 1px solid var(--d-border);
  border-left: 3px solid var(--d-primary);
  border-radius: var(--d-radius);
  background: var(--d-panel);
}

.docroute-callout-title {
  margin-bottom: 4px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.docroute-callout-body > *:last-child {
  margin-bottom: 0;
}

.docroute-callout.is-note {
  border-left-color: #8ab4f8;
  background: rgba(138, 180, 248, 0.08);
  background: color-mix(in srgb, #8ab4f8 10%, var(--d-panel));
}

.docroute-callout.is-tip {
  border-left-color: #9ecb8f;
  background: rgba(158, 203, 143, 0.08);
  background: color-mix(in srgb, #9ecb8f 10%, var(--d-panel));
}

.docroute-callout.is-important {
  border-left-color: #c792ea;
  background: rgba(199, 146, 234, 0.09);
  background: color-mix(in srgb, #c792ea 11%, var(--d-panel));
}

.docroute-callout.is-warning {
  border-left-color: #e0a878;
  background: rgba(224, 168, 120, 0.09);
  background: color-mix(in srgb, #e0a878 11%, var(--d-panel));
}

.docroute-callout.is-caution {
  border-left-color: #e39aa6;
  background: rgba(227, 154, 166, 0.09);
  background: color-mix(in srgb, #e39aa6 11%, var(--d-panel));
}

.docroute-content hr {
  margin: 32px 0;
  border: 0;
  border-top: 1px solid var(--d-border);
}

.docroute-content img {
  max-width: 100%;
  border-radius: var(--d-radius);
}

.docroute-table-wrap {
  overflow-x: auto;
  border: 1px solid var(--d-border);
  border-radius: var(--d-radius);
}

.docroute-content table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 14px;
}

.docroute-content th,
.docroute-content td {
  padding: 9px 14px;
  border-bottom: 1px solid var(--d-border);
  border-left: 1px solid var(--d-border);
  text-align: left;
}

.docroute-content th:first-child,
.docroute-content td:first-child {
  border-left: 0;
}

.docroute-content tr:last-child td {
  border-bottom: 0;
}

.docroute-content th {
  background: var(--d-panel-2);
  font-weight: 600;
}

.docroute-pager {
  display: flex;
  gap: 12px;
  margin-top: 56px;
  padding-top: 24px;
  border-top: 1px solid var(--d-border);
}

.docroute-pager-link {
  flex: 1 1 0;
  min-width: 0;
  padding: 12px 16px;
  border: 1px solid var(--d-border);
  border-radius: var(--d-radius);
  background: var(--d-panel);
}

.docroute-pager-link:hover {
  border-color: var(--d-primary);
}

.docroute-pager-link.is-next {
  text-align: right;
}

.docroute-pager-label {
  display: block;
  margin-bottom: 2px;
  color: var(--d-muted);
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.docroute-pager-name {
  display: block;
  overflow: hidden;
  color: var(--d-text);
  font-size: 14px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.docroute-state {
  padding: 56px 0;
  color: var(--d-muted);
  font-size: 14px;
}

.docroute-state strong {
  display: block;
  margin-bottom: 6px;
  color: var(--d-text);
  font-size: 15px;
}

.docroute-state p {
  margin: 0 0 8px;
}

.docroute-state code {
  padding: 2px 6px;
  border: 1px solid var(--d-border);
  border-radius: 7px;
  background: var(--d-panel-2);
  font-family: var(--d-mono);
  font-size: 12.5px;
}

.docroute-skeleton {
  padding-top: 4px;
}

.docroute-skeleton-line,
.docroute-skeleton-block {
  background: var(--d-panel);
  background: linear-gradient(90deg, var(--d-panel) 25%, var(--d-panel-2) 50%, var(--d-panel) 75%);
  background-size: 200% 100%;
  border-radius: var(--d-radius);
  animation: docroute-shimmer 1.4s linear infinite;
}

.docroute-skeleton-line {
  height: 12px;
  margin-bottom: 14px;
}

.docroute-skeleton-title {
  width: 42%;
  height: 26px;
  margin-bottom: 30px;
}

.docroute-skeleton-line:nth-of-type(2) {
  width: 96%;
}

.docroute-skeleton-line:nth-of-type(3) {
  width: 88%;
}

.docroute-skeleton-line:nth-of-type(4) {
  width: 94%;
}

.docroute-skeleton-line:nth-of-type(5) {
  width: 64%;
}

.docroute-skeleton-block {
  height: 128px;
  margin: 26px 0;
}

.docroute-skeleton-line:nth-of-type(7) {
  width: 90%;
}

.docroute-skeleton-line:nth-of-type(8) {
  width: 97%;
}

.docroute-skeleton-line:nth-of-type(9) {
  width: 70%;
  margin-bottom: 0;
}

@keyframes docroute-shimmer {
  from {
    background-position: 200% 0;
  }

  to {
    background-position: -200% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .docroute-skeleton-line,
  .docroute-skeleton-block {
    animation: none;
  }
}

@media (max-width: 900px) {
  .docroute-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    width: 280px;
    transform: translateX(-100%);
    transition: transform 0.18s ease;
  }

  .docroute.is-open .docroute-sidebar {
    transform: none;
  }

  .docroute-overlay {
    position: fixed;
    inset: 0;
    z-index: 15;
    display: none;
    background: rgba(0, 0, 0, 0.5);
  }

  .docroute.is-open .docroute-overlay {
    display: block;
  }

  .docroute-menu-btn {
    display: grid;
  }

  .docroute-content {
    padding: 28px 18px 72px;
  }

  .docroute-content h1 {
    font-size: 1.7rem;
  }
}
`;

  var state = {
    config: null,
    root: null,
    nav: null,
    content: null,
    crumbs: null,
    current: null,
    theme: "dark",
    search: null,
    searchEmpty: null,
    token: 0,
    options: {},
    contentIndex: {},
    indexPromise: null,
    indexReady: false,
    shortcutBound: false
  };

  var markedPromise = null;
  var highlightPromise = null;

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (char) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
    });
  }

  function normalizeText(value) {
    return String(value == null ? "" : value)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .trim();
  }

  function slugify(value) {
    var slug = String(value)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return slug || "page";
  }

  function resolveUrl(base, url) {
    try {
      return new URL(url, base || document.baseURI).href;
    } catch (error) {
      return url;
    }
  }

  function isAbsoluteUrl(url) {
    return /^[a-z][a-z0-9+.-]*:/i.test(String(url));
  }

  function normalizeFooter(footer, footerUrl) {
    if (footer === false) return false;
    if (footer && typeof footer === "object") {
      var text = footer.text || footer.label || "Powered by docroute";
      var url = footer.url || footer.href || footerUrl || null;
      return { text: String(text), url: url ? String(url) : null };
    }
    if (typeof footer === "string") {
      if (!footer) return false;
      return { text: footer, url: footerUrl ? String(footerUrl) : null };
    }
    return { text: "Powered by docroute", url: "https://github.com/alesis-buzz/docroute" };
  }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var script = document.createElement("script");
      script.src = src;
      script.async = true;
      script.onload = resolve;
      script.onerror = function () {
        reject(new Error("could not load " + src));
      };
      document.head.appendChild(script);
    });
  }

  function ensureStyles() {
    if (document.getElementById("docroute-styles")) return;
    var links = document.querySelectorAll('link[rel="stylesheet"]');
    for (var i = 0; i < links.length; i++) {
      var href = links[i].getAttribute("href") || "";
      if (/(^|\/)docroute(\.min)?\.css(\?|#|$)/.test(href)) return;
    }
    var style = document.createElement("style");
    style.id = "docroute-styles";
    style.textContent = FALLBACK_CSS;
    document.head.appendChild(style);
  }

  function ensureMarked() {
    if (window.marked && typeof window.marked.parse === "function") {
      return Promise.resolve(window.marked);
    }
    if (!markedPromise) {
      markedPromise = loadScript(MARKED_URL)
        .then(function () {
          if (!window.marked || typeof window.marked.parse !== "function") {
            throw new Error("marked did not initialize");
          }
          return window.marked;
        })
        .catch(function () {
          markedPromise = null;
          throw new Error("DocRoute could not load the Markdown parser from " + MARKED_URL);
        });
    }
    return markedPromise;
  }

  function ensureHighlight() {
    if (window.hljs) return Promise.resolve(window.hljs);
    if (!highlightPromise) {
      highlightPromise = loadScript(HIGHLIGHT_URL)
        .then(function () {
          return window.hljs || null;
        })
        .catch(function () {
          highlightPromise = null;
          return null;
        });
    }
    return highlightPromise;
  }

  function highlightBlocks(container, hljs) {
    if (!hljs || typeof hljs.highlight !== "function") return;
    var blocks = container.querySelectorAll("pre code");
    for (var i = 0; i < blocks.length; i++) {
      var code = blocks[i];
      if (code.classList.contains("hljs")) continue;
      var match = /(?:^|\s)language-([\w-]+)/.exec(code.className);
      var language = match && match[1];
      var known = language && typeof hljs.getLanguage === "function" && hljs.getLanguage(language);
      var result = known
        ? hljs.highlight(code.textContent, { language: language, ignoreIllegals: true })
        : hljs.highlightAuto(code.textContent);
      code.innerHTML = result.value;
      code.classList.add("hljs");
      if (result.language) code.setAttribute("data-language", result.language);
    }
  }

  function fetchText(url) {
    return fetch(url, { credentials: "same-origin" }).then(function (response) {
      if (!response.ok) {
        throw new Error("HTTP " + response.status + " " + response.statusText + " (" + url + ")");
      }
      return response.text();
    });
  }

  function sanitize(html) {
    var template = document.createElement("template");
    template.innerHTML = html;
    template.content.querySelectorAll("script, object, embed, base, meta").forEach(function (node) {
      node.remove();
    });
    template.content.querySelectorAll("*").forEach(function (element) {
      Array.prototype.slice.call(element.attributes).forEach(function (attribute) {
        var name = attribute.name.toLowerCase();
        if (name.indexOf("on") === 0) {
          element.removeAttribute(attribute.name);
          return;
        }
        if (name === "href" || name === "src" || name === "xlink:href") {
          var value = attribute.value.replace(/[\s\u0000-\u001f]/g, "").toLowerCase();
          if (value.indexOf("javascript:") === 0 || value.indexOf("data:text/html") === 0) {
            element.removeAttribute(attribute.name);
          }
        }
      });
    });
    return template.innerHTML;
  }

  function decorateTables(container) {
    var tables = container.querySelectorAll("table");
    for (var i = 0; i < tables.length; i++) {
      var table = tables[i];
      var parent = table.parentNode;
      if (parent && parent.classList && parent.classList.contains("docroute-table-wrap")) continue;
      var wrapper = document.createElement("div");
      wrapper.className = "docroute-table-wrap";
      parent.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    }
  }

  function copyText(text) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      return navigator.clipboard.writeText(text).then(
        function () {
          return true;
        },
        function () {
          return legacyCopy(text);
        }
      );
    }
    return Promise.resolve(legacyCopy(text));
  }

  function legacyCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.top = "-1000px";
    document.body.appendChild(area);
    area.select();
    var copied = false;
    try {
      copied = document.execCommand("copy");
    } catch (error) {
      copied = false;
    }
    document.body.removeChild(area);
    return copied;
  }

  function decorateCode(container) {
    var blocks = container.querySelectorAll("pre");
    for (var i = 0; i < blocks.length; i++) {
      var pre = blocks[i];
      var parent = pre.parentNode;
      if (parent && parent.classList && parent.classList.contains("docroute-code")) continue;
      var wrapper = document.createElement("div");
      wrapper.className = "docroute-code";
      parent.insertBefore(wrapper, pre);
      wrapper.appendChild(pre);
      var button = document.createElement("button");
      button.type = "button";
      button.className = "docroute-copy-btn";
      button.textContent = "Copy";
      button.setAttribute("aria-label", "Copy code");
      wrapper.appendChild(button);
    }
  }

  function copyClick(event) {
    var button = event.target.closest ? event.target.closest(".docroute-copy-btn") : null;
    if (!button) return;
    var wrapper = button.closest(".docroute-code");
    var code = wrapper ? wrapper.querySelector("pre code") : null;
    if (!code) return;
    copyText(code.textContent).then(function (copied) {
      button.textContent = copied ? "Copied" : "Copy failed";
      button.classList.toggle("is-copied", copied);
      setTimeout(function () {
        button.textContent = "Copy";
        button.classList.remove("is-copied");
      }, 1600);
    });
  }

  var CALLOUT_TITLES = {
    note: "Note",
    tip: "Tip",
    important: "Important",
    warning: "Warning",
    caution: "Caution"
  };

  function decorateCallouts(container) {
    var quotes = container.querySelectorAll("blockquote");
    for (var i = 0; i < quotes.length; i++) {
      var quote = quotes[i];
      var first = quote.querySelector("p");
      if (!first) continue;
      var text = first.textContent || "";
      var match = /^\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*/i.exec(text);
      if (!match) continue;
      var type = match[1].toLowerCase();
      var marker = match[0];
      if (first.firstChild && first.firstChild.nodeType === 3) {
        first.firstChild.nodeValue = first.firstChild.nodeValue.replace(marker, "");
      } else {
        first.textContent = text.replace(marker, "");
      }
      if (!first.textContent.trim() && first.parentNode === quote) {
        var next = first.nextSibling;
        first.parentNode.removeChild(first);
        if (!quote.children.length && next) quote.appendChild(next);
      }
      var callout = document.createElement("div");
      callout.className = "docroute-callout is-" + type;
      var title = document.createElement("div");
      title.className = "docroute-callout-title";
      title.textContent = CALLOUT_TITLES[type] || type;
      var body = document.createElement("div");
      body.className = "docroute-callout-body";
      while (quote.firstChild) body.appendChild(quote.firstChild);
      callout.appendChild(title);
      callout.appendChild(body);
      quote.parentNode.replaceChild(callout, quote);
    }
  }

  function applyFavicon(url) {
    if (!url) return;
    var link = document.querySelector('link[rel="icon"]');
    if (!link) {
      link = document.createElement("link");
      link.rel = "icon";
      document.head.appendChild(link);
    }
    link.href = url;
  }

  function searchContentEnabled() {
    return state.options.searchContent !== false;
  }

  function ensureContentIndex() {
    if (state.indexReady) return Promise.resolve(state.contentIndex);
    if (state.indexPromise) return state.indexPromise;
    if (!state.config || !state.config.pages.length) {
      state.indexReady = true;
      return Promise.resolve(state.contentIndex);
    }
    state.indexPromise = Promise.all(
      state.config.pages.map(function (page) {
        if (state.contentIndex[page.slug]) return Promise.resolve(null);
        return fetchText(page.url)
          .then(function (markdown) {
            state.contentIndex[page.slug] = normalizeText(markdown);
          })
          .catch(function () {
            state.contentIndex[page.slug] = "";
          });
      })
    ).then(function () {
      state.indexReady = true;
      return state.contentIndex;
    });
    return state.indexPromise;
  }

  function scheduleContentIndex() {
    if (!searchContentEnabled()) return;
    var kick = function () {
      ensureContentIndex().then(function () {
        if (state.search && state.search.value) filterNav();
      });
    };
    if (typeof window.requestIdleCallback === "function") window.requestIdleCallback(kick);
    else setTimeout(kick, 1500);
  }

  function isTypingTarget(element) {
    if (!element) return false;
    var tag = (element.tagName || "").toUpperCase();
    return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || !!element.isContentEditable;
  }

  function shortcutsEnabled() {
    return state.options.shortcuts !== false;
  }

  function onShortcutKey(event) {
    if (!shortcutsEnabled() || !state.config) return;
    if (event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) return;
    var active = document.activeElement;
    if (event.key === "/" && !isTypingTarget(active)) {
      if (state.search) {
        event.preventDefault();
        state.search.focus();
      }
      return;
    }
    if (event.key === "Escape" && active === state.search) {
      state.search.value = "";
      filterNav();
      state.search.blur();
      return;
    }
    if ((event.key === "ArrowRight" || event.key === "ArrowLeft") && !isTypingTarget(active)) {
      if (!state.current) return;
      var target = state.config.pages[state.current.index + (event.key === "ArrowRight" ? 1 : -1)];
      if (target) {
        event.preventDefault();
        go(target.slug);
      }
    }
  }

  function bindShortcuts() {
    if (state.shortcutBound) return;
    state.shortcutBound = true;
    document.addEventListener("keydown", onShortcutKey);
  }

  function loadConfig(input) {
    if (Array.isArray(input) || (input && typeof input === "object")) {
      return Promise.resolve({ raw: input, baseUrl: document.baseURI });
    }
    if (typeof input !== "string" || !input.trim()) {
      return Promise.reject(new Error("InitDocs expects a JSON URL, a JSON string or an array."));
    }
    var text = input.trim();
    if (text.charAt(0) === "[" || text.charAt(0) === "{") {
      try {
        return Promise.resolve({ raw: JSON.parse(text), baseUrl: document.baseURI });
      } catch (error) {
        return Promise.reject(new Error("InitDocs received a JSON string that could not be parsed."));
      }
    }
    var url = resolveUrl(document.baseURI, text);
    return fetchText(url).then(function (body) {
      try {
        return { raw: JSON.parse(body), baseUrl: url };
      } catch (error) {
        throw new Error("The file at " + url + " is not valid JSON.");
      }
    });
  }

  function normalize(raw, baseUrl) {
    var meta = {};
    var items = [];
    if (Array.isArray(raw)) {
      items = raw;
    } else if (raw && typeof raw === "object") {
      meta.name = raw.name || raw.title || "Documentation";
      meta.primary = raw.primary || raw.primaryColor || raw.primary_color || null;
      meta.theme = raw.theme === "light" ? "light" : null;
      meta.logo = raw.logo || raw.logoUrl || raw.logo_url || null;
      meta.favicon = raw.favicon || raw.icon || null;
      meta.footer = raw.footer !== undefined ? raw.footer : raw.footerText !== undefined ? raw.footerText : raw.footer_text !== undefined ? raw.footer_text : undefined;
      meta.footerUrl = raw.footerUrl || raw.footer_url || null;
      items = Array.isArray(raw.sections) ? raw.sections : Array.isArray(raw.items) ? raw.items : [];
      if (raw.base_url || raw.baseUrl) {
        var base = String(raw.base_url || raw.baseUrl);
        if (base.charAt(base.length - 1) !== "/") base += "/";
        baseUrl = resolveUrl(baseUrl, base);
      }
      if (meta.logo && !isAbsoluteUrl(meta.logo)) meta.logo = resolveUrl(baseUrl, meta.logo);
      if (meta.favicon && !isAbsoluteUrl(meta.favicon)) meta.favicon = resolveUrl(baseUrl, meta.favicon);
      if (typeof meta.footerUrl === "string" && meta.footerUrl && !isAbsoluteUrl(meta.footerUrl)) {
        meta.footerUrl = resolveUrl(baseUrl, meta.footerUrl);
      }
    }
    if (!meta.name) meta.name = "Documentation";
    if (meta.footer === undefined) meta.footer = undefined;

    var pages = [];
    var links = [];
    var usedSlugs = {};

    function walk(list, sectionName) {
      var children = [];
      list.forEach(function (entry) {
        if (!entry || typeof entry !== "object") return;
        var type = entry.type || (entry.pages ? "section" : entry.md_url ? "page" : entry.url ? "link" : null);
        if (type === "section") {
          var childSection = entry.name || "";
          children.push({
            type: "section",
            name: childSection,
            children: walk(entry.pages || entry.items || [], childSection)
          });
          return;
        }
        if (type === "link") {
          var link = {
            type: "link",
            name: entry.name || entry.url,
            url: isAbsoluteUrl(entry.url) ? entry.url : resolveUrl(baseUrl, entry.url)
          };
          links.push(link);
          children.push(link);
          return;
        }
        if (type === "page" || entry.md_url) {
          var slug = slugify(entry.slug || entry.name || "page");
          if (usedSlugs[slug]) {
            var index = 2;
            while (usedSlugs[slug + "-" + index]) index++;
            slug = slug + "-" + index;
          }
          usedSlugs[slug] = true;
          var page = {
            type: "page",
            name: entry.name || slug,
            section: sectionName || "",
            url: isAbsoluteUrl(entry.md_url) ? entry.md_url : resolveUrl(baseUrl, entry.md_url),
            slug: slug
          };
          page.index = pages.length;
          pages.push(page);
          children.push(page);
        }
      });
      return children;
    }

    var sections = walk(items, "");
    var bySlug = {};
    var byUrl = {};
    pages.forEach(function (page) {
      bySlug[page.slug] = page;
      byUrl[page.url.split("#")[0]] = page;
    });

    return {
      name: meta.name,
      primary: meta.primary,
      theme: meta.theme,
      logo: meta.logo || null,
      favicon: meta.favicon || null,
      footer: normalizeFooter(meta.footer, meta.footerUrl),
      sections: sections,
      pages: pages,
      links: links,
      bySlug: bySlug,
      byUrl: byUrl
    };
  }

  function resolveRoot(options) {
    if (options.target) {
      var target = typeof options.target === "string" ? document.querySelector(options.target) : options.target;
      if (target) return target;
    }
    return document.getElementById("docroute") || document.body;
  }

  function buildShell(root, config, theme) {
    root.classList.add("docroute");
    root.setAttribute("data-docroute-theme", theme);
    root.innerHTML =
      '<aside class="docroute-sidebar">' +
      '<div class="docroute-brand"><span class="docroute-brand-mark">M</span><span class="docroute-brand-name"></span></div>' +
      '<div class="docroute-search"><input type="search" class="docroute-search-input" placeholder="Search…" aria-label="Search pages"></div>' +
      '<nav class="docroute-nav"></nav>' +
      '<div class="docroute-search-empty" hidden>No results</div>' +
      '<div class="docroute-sidebar-footer"><a href="https://github.com/alesis-buzz/docroute" target="_blank" rel="noopener noreferrer">Powered by docroute</a></div>' +
      "</aside>" +
      '<div class="docroute-overlay"></div>' +
      '<div class="docroute-main">' +
      '<header class="docroute-topbar">' +
      '<button class="docroute-icon-btn docroute-menu-btn" type="button" aria-label="Toggle navigation">☰</button>' +
      '<div class="docroute-crumbs"></div>' +
      '<div class="docroute-actions">' +
      '<button class="docroute-icon-btn docroute-theme-btn" type="button"></button>' +
      "</div>" +
      "</header>" +
      '<main class="docroute-content"></main>' +
      "</div>";

    var brandMark = root.querySelector(".docroute-brand-mark");
    if (config.logo) {
      var logoImg = document.createElement("img");
      logoImg.className = "docroute-brand-logo";
      logoImg.src = config.logo;
      logoImg.alt = config.name;
      brandMark.parentNode.replaceChild(logoImg, brandMark);
    } else {
      brandMark.textContent = config.name.charAt(0).toUpperCase();
    }
    root.querySelector(".docroute-brand-name").textContent = config.name;
    var footer = root.querySelector(".docroute-sidebar-footer");
    if (config.footer === false) {
      footer.hidden = true;
    } else if (config.footer) {
      footer.innerHTML = "";
      if (config.footer.url) {
        var footerLink = document.createElement("a");
        footerLink.href = config.footer.url;
        footerLink.target = "_blank";
        footerLink.rel = "noopener noreferrer";
        footerLink.textContent = config.footer.text;
        footer.appendChild(footerLink);
      } else {
        footer.textContent = config.footer.text;
      }
    }
    root.querySelector(".docroute-brand").addEventListener("click", function () {
      if (config.pages[0]) go(config.pages[0].slug);
    });
    state.nav = root.querySelector(".docroute-nav");
    state.search = root.querySelector(".docroute-search-input");
    state.searchEmpty = root.querySelector(".docroute-search-empty");
    state.content = root.querySelector(".docroute-content");
    state.crumbs = root.querySelector(".docroute-crumbs");
    state.nav.appendChild(buildNav(config.sections));
    state.search.addEventListener("input", filterNav);
    state.search.setAttribute("title", "Press / to search, Esc to clear");
    state.content.addEventListener("click", copyClick);
    bindShortcuts();

    root.querySelector(".docroute-theme-btn").addEventListener("click", function () {
      applyTheme(state.theme === "dark" ? "light" : "dark");
    });
    root.querySelector(".docroute-menu-btn").addEventListener("click", function () {
      root.classList.toggle("is-open");
    });
    root.querySelector(".docroute-overlay").addEventListener("click", function () {
      root.classList.remove("is-open");
    });
    root.addEventListener("click", function (event) {
      var link = event.target.closest ? event.target.closest('a[href^="#/"]') : null;
      if (link) root.classList.remove("is-open");
    });
    updateThemeButton();
  }

  function buildNav(items) {
    var fragment = document.createDocumentFragment();
    (items || []).forEach(function (item) {
      if (item.type === "section") {
        var section = document.createElement("div");
        section.className = "docroute-section";
        var title = document.createElement("div");
        title.className = "docroute-section-title";
        title.textContent = item.name;
        title.dataset.name = normalizeText(item.name);
        section.appendChild(title);
        section.appendChild(buildNav(item.children));
        fragment.appendChild(section);
        return;
      }
      var link = document.createElement("a");
      link.className = "docroute-item";
      link.dataset.name = normalizeText(item.name);
      if (item.type === "page") {
        link.href = "#/" + item.slug;
        link.dataset.slug = item.slug;
        link.title = item.name;
        link.appendChild(document.createTextNode(item.name));
      } else {
        link.href = item.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.title = item.name;
        link.appendChild(document.createTextNode(item.name));
        var glyph = document.createElement("span");
        glyph.className = "docroute-external-glyph";
        glyph.textContent = "↗";
        link.appendChild(glyph);
      }
      fragment.appendChild(link);
    });
    return fragment;
  }

  function filterNav() {
    if (!state.search || !state.nav) return;
    var terms = normalizeText(state.search.value).split(/\s+/).filter(Boolean);
    var all = terms.length === 0;
    var useContent = searchContentEnabled() && !all;

    if (useContent && !state.indexReady && !state.indexPromise) {
      ensureContentIndex().then(function () {
        filterNav();
      });
    }

    function matches(name) {
      if (!name) return false;
      for (var i = 0; i < terms.length; i++) {
        if (name.indexOf(terms[i]) === -1) return false;
      }
      return true;
    }

    function matchesContent(slug) {
      if (!useContent || !slug) return false;
      var haystack = state.contentIndex[slug];
      if (haystack === undefined) return false;
      for (var i = 0; i < terms.length; i++) {
        if (haystack.indexOf(terms[i]) === -1) return false;
      }
      return true;
    }

    function walk(section, ancestorMatch) {
      var title = section.querySelector(":scope > .docroute-section-title");
      var titleMatch = ancestorMatch || (!!title && matches(title.dataset.name));
      var visibleChildren = 0;
      var children = section.children;
      for (var i = 0; i < children.length; i++) {
        var child = children[i];
        if (child.classList.contains("docroute-section")) {
          var sectionVisible = walk(child, titleMatch);
          child.hidden = !sectionVisible;
          if (sectionVisible) visibleChildren++;
        } else if (child.classList.contains("docroute-item")) {
          var itemVisible =
            all || titleMatch || matches(child.dataset.name) || matchesContent(child.dataset.slug);
          child.hidden = !itemVisible;
          if (itemVisible) visibleChildren++;
        }
      }
      var visible = all || titleMatch || visibleChildren > 0;
      if (title) title.hidden = !visible;
      return visible;
    }

    var visibleSections = 0;
    var sections = state.nav.children;
    for (var i = 0; i < sections.length; i++) {
      var section = sections[i];
      if (!section.classList.contains("docroute-section")) continue;
      var visible = walk(section, false);
      section.hidden = !visible;
      if (visible) visibleSections++;
    }
    if (visibleSections === 0 && useContent && !state.indexReady) {
      state.searchEmpty.textContent = "Indexing…";
      state.searchEmpty.hidden = false;
    } else {
      state.searchEmpty.textContent = "No results";
      state.searchEmpty.hidden = visibleSections > 0;
    }
  }

  function applyTheme(theme) {
    state.theme = theme === "light" ? "light" : "dark";
    if (state.root) state.root.setAttribute("data-docroute-theme", state.theme);
    updateThemeButton();
    try {
      localStorage.setItem(THEME_KEY, state.theme);
    } catch (error) {}
  }

  function applyPrimary(color) {
    if (!state.root || !color) return;
    if (!/^(#[0-9a-f]{3,8}|rgba?\(|hsla?\()/i.test(String(color).trim())) return;
    state.root.style.setProperty("--d-primary", String(color).trim());
  }

  function updateThemeButton() {
    if (!state.root) return;
    var button = state.root.querySelector(".docroute-theme-btn");
    if (!button) return;
    var next = state.theme === "dark" ? "light" : "dark";
    button.textContent = state.theme === "dark" ? "☀" : "☾";
    button.setAttribute("aria-label", "Switch to " + next + " theme");
    button.title = "Switch to " + next + " theme";
  }

  function storedTheme() {
    try {
      return localStorage.getItem(THEME_KEY);
    } catch (error) {
      return null;
    }
  }

  function slugFromHash() {
    var hash = window.location.hash || "";
    if (hash.indexOf("#/") !== 0) return null;
    var slug = hash.slice(2).split("?")[0];
    try {
      slug = decodeURIComponent(slug);
    } catch (error) {}
    return slug || null;
  }

  function setCrumbs(page) {
    state.crumbs.innerHTML = "";
    var parts = [page.section, page.name].filter(Boolean);
    parts.forEach(function (part, index) {
      if (index > 0) {
        var separator = document.createElement("span");
        separator.className = "docroute-crumb-sep";
        separator.textContent = "·";
        state.crumbs.appendChild(separator);
      }
      var span = document.createElement("span");
      span.textContent = part;
      if (index === parts.length - 1) span.className = "docroute-crumb-current";
      state.crumbs.appendChild(span);
    });
  }

  function markActive(slug) {
    var items = state.nav.querySelectorAll(".docroute-item[data-slug]");
    for (var i = 0; i < items.length; i++) {
      items[i].classList.toggle("is-active", items[i].dataset.slug === slug);
    }
  }

  function buildPager(page) {
    var pager = document.createElement("nav");
    pager.className = "docroute-pager";
    var previous = state.config.pages[page.index - 1];
    var next = state.config.pages[page.index + 1];
    [previous ? { page: previous, label: "Previous" } : null, next ? { page: next, label: "Next", forward: true } : null]
      .filter(Boolean)
      .forEach(function (entry) {
        var link = document.createElement("a");
        link.className = "docroute-pager-link" + (entry.forward ? " is-next" : "");
        link.href = "#/" + entry.page.slug;
        var label = document.createElement("span");
        label.className = "docroute-pager-label";
        label.textContent = entry.label;
        var name = document.createElement("span");
        name.className = "docroute-pager-name";
        name.textContent = entry.page.name;
        link.appendChild(label);
        link.appendChild(name);
        pager.appendChild(link);
      });
    return pager.children.length ? pager : null;
  }

  function stateMessage(title, detail, hint) {
    var html = '<div class="docroute-state"><strong>' + escapeHtml(title) + "</strong>";
    if (detail) html += "<p>" + escapeHtml(detail) + "</p>";
    if (hint) html += "<p><code>" + escapeHtml(hint) + "</code></p>";
    return html + "</div>";
  }

  function skeletonHtml() {
    var line = '<div class="docroute-skeleton-line"></div>';
    return (
      '<div class="docroute-skeleton" role="status" aria-label="Loading page">' +
      '<div class="docroute-skeleton-line docroute-skeleton-title"></div>' +
      line +
      line +
      line +
      line +
      '<div class="docroute-skeleton-block"></div>' +
      line +
      line +
      line +
      "</div>"
    );
  }

  function showPage(slug) {
    var page = state.config.bySlug[slug];
    if (!page) {
      document.title = "Page not found · " + state.config.name;
      state.content.innerHTML = stateMessage("Page not found", 'No page is registered under the slug "' + slug + '".');
      return;
    }
    state.current = page;
    var token = ++state.token;
    markActive(slug);
    setCrumbs(page);
    document.title = page.name + " · " + state.config.name;
    state.content.setAttribute("aria-busy", "true");
    state.content.innerHTML = skeletonHtml();
    window.scrollTo(0, 0);

    ensureMarked()
      .then(function (marked) {
        return fetchText(page.url).then(function (markdown) {
          return { marked: marked, markdown: markdown };
        });
      })
      .then(function (result) {
        if (token !== state.token) return;
        state.content.setAttribute("aria-busy", "false");
        state.content.innerHTML =
          '<article class="docroute-article">' + sanitize(result.marked.parse(result.markdown, { gfm: true })) + "</article>";
        var article = state.content.querySelector(".docroute-article");
        if (searchContentEnabled()) state.contentIndex[page.slug] = normalizeText(result.markdown);
        if (article) {
          decorateTables(article);
          decorateCallouts(article);
          if (state.options.copy !== false) decorateCode(article);
        }
        if (article && state.options.highlight !== false && article.querySelector("pre code")) {
          ensureHighlight().then(function (hljs) {
            if (token !== state.token) return;
            highlightBlocks(article, hljs);
          });
        }
        var pager = buildPager(page);
        if (pager) state.content.appendChild(pager);
      })
      .catch(function (error) {
        if (token !== state.token) return;
        state.content.setAttribute("aria-busy", "false");
        state.content.innerHTML = stateMessage(
          "Could not load this page",
          error.message,
          page.url
        );
      });
  }

  function go(slug) {
    var target = "#/" + slug;
    if (window.location.hash === target) showPage(slug);
    else window.location.hash = target;
  }

  function contentClick(event) {
    var anchor = event.target.closest ? event.target.closest("a") : null;
    if (!anchor) return;
    var href = anchor.getAttribute("href") || "";
    if (!href || href.charAt(0) === "#" || isAbsoluteUrl(href)) return;
    var page = state.current;
    if (!page) return;
    var resolved = resolveUrl(page.url, href).split("#")[0];
    var target = state.config.byUrl[resolved];
    if (target) {
      event.preventDefault();
      go(target.slug);
    }
  }

  function onHashChange() {
    var slug = slugFromHash();
    if (slug) showPage(slug);
  }

  function fatal(root, error) {
    root.classList.add("docroute");
    if (!root.getAttribute("data-docroute-theme")) root.setAttribute("data-docroute-theme", state.theme);
    root.innerHTML =
      '<div class="docroute-main"><main class="docroute-content">' +
      stateMessage("DocRoute could not start", error && error.message ? error.message : String(error)) +
      "</main></div>";
  }

  function InitDocs(input, options) {
    options = options || {};
    state.options = options;
    ensureStyles();
    var root = resolveRoot(options);
    state.root = root;
    var initialTheme = storedTheme() || options.theme || "dark";
    root.setAttribute("data-docroute-theme", initialTheme === "light" ? "light" : "dark");

    return loadConfig(input)
      .then(function (loaded) {
        var config = normalize(loaded.raw, loaded.baseUrl);
        if (options.logo) config.logo = options.logo;
        if (options.favicon) config.favicon = options.favicon;
        if (options.footer !== undefined) {
          config.footer =
            options.footer === false ? false : typeof options.footer === "string" ? { text: options.footer, url: options.footerUrl || null } : options.footer;
        } else if (options.footerUrl) {
          config.footer = config.footer === false ? false : { text: (config.footer && config.footer.text) || "Powered by docroute", url: options.footerUrl };
        }
        state.config = config;
        state.contentIndex = {};
        state.indexPromise = null;
        state.indexReady = false;
        state.theme = initialTheme === "light" ? "light" : "dark";
        if (config.theme && !storedTheme() && !options.theme) state.theme = config.theme;
        buildShell(root, config, state.theme);
        applyPrimary(options.primary || config.primary);
        applyFavicon(config.favicon);
        state.content.addEventListener("click", contentClick);
        window.addEventListener("hashchange", onHashChange);
        var slug = slugFromHash() || (config.pages[0] && config.pages[0].slug);
        if (slug) showPage(slug);
        else state.content.innerHTML = stateMessage("Nothing to show", "This configuration has no pages.");
        scheduleContentIndex();
        return api;
      })
      .catch(function (error) {
        if (!state.config) fatal(root, error);
        throw error;
      });
  }

  function autoInit() {
    var scripts = document.querySelectorAll("script[data-docroute]");
    for (var i = 0; i < scripts.length; i++) {
      var script = scripts[i];
      var input = script.getAttribute("data-docroute");
      if (!input) continue;
      var footerAttr = script.getAttribute("data-footer");
      InitDocs(input, {
        target: script.getAttribute("data-target") || null,
        primary: script.getAttribute("data-primary") || null,
        theme: script.getAttribute("data-theme") || null,
        logo: script.getAttribute("data-logo") || null,
        favicon: script.getAttribute("data-favicon") || script.getAttribute("data-icon") || null,
        footer: footerAttr === null ? undefined : footerAttr === "false" ? false : footerAttr,
        footerUrl: script.getAttribute("data-footer-url") || null,
        highlight: script.getAttribute("data-highlight") === "false" ? false : null,
        copy: script.getAttribute("data-copy") === "false" ? false : null,
        searchContent: script.getAttribute("data-search-content") === "false" ? false : null,
        shortcuts: script.getAttribute("data-shortcuts") === "false" ? false : null
      }).catch(function (error) {
        if (window.console && console.error) console.error(error);
      });
    }
  }

  var api = {
    version: VERSION,
    InitDocs: InitDocs,
    setTheme: applyTheme,
    setPrimary: applyPrimary,
    getConfig: function () {
      return state.config;
    },
    go: go
  };

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", autoInit);
    else autoInit();
  }

  return api;
});
