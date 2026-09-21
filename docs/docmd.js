(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.docmd = factory();
})(typeof globalThis !== "undefined" ? globalThis : typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var VERSION = "1.0.0";
  var MARKED_URL = "https://cdn.jsdelivr.net/npm/marked@12/marked.min.js";
  var HIGHLIGHT_URL = "https://cdn.jsdelivr.net/npm/@highlightjs/cdn-assets@11/highlight.min.js";
  var THEME_KEY = "docmd-theme";
  var FALLBACK_CSS = `.docmd {
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

.docmd[data-docmd-theme="light"] {
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

.docmd *,
.docmd *::before,
.docmd *::after {
  box-sizing: border-box;
}

.docmd ::selection {
  background: var(--d-primary-soft);
  color: var(--d-text);
}

.docmd a {
  color: inherit;
  text-decoration: none;
}

.docmd button {
  font: inherit;
}

.docmd [hidden] {
  display: none !important;
}

.docmd-sidebar {
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

.docmd-sidebar::-webkit-scrollbar {
  width: 10px;
}

.docmd-sidebar::-webkit-scrollbar-thumb {
  background: var(--d-border);
  border: 3px solid var(--d-panel);
  border-radius: 999px;
}

.docmd-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px 18px 10px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
  cursor: pointer;
}

.docmd-brand-mark {
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

.docmd-brand-name {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.docmd-search {
  padding: 2px 10px 10px;
}

.docmd-search-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--d-border);
  border-radius: var(--d-radius);
  background: var(--d-bg);
  color: var(--d-text);
  font-family: inherit;
  font-size: 13.5px;
}

.docmd-search-input::placeholder {
  color: var(--d-muted);
}

.docmd-search-input:focus {
  border-color: var(--d-primary);
  box-shadow: 0 0 0 3px var(--d-primary-soft);
  outline: none;
}

.docmd-search-empty {
  padding: 8px 20px;
  color: var(--d-muted);
  font-size: 13px;
}

.docmd-nav {
  padding: 6px 10px 28px;
}

.docmd-section + .docmd-section {
  margin-top: 20px;
}

.docmd-section-title {
  padding: 6px 10px;
  color: var(--d-muted);
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.docmd-item {
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

.docmd-item > span:first-child {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.docmd-item:hover {
  background: var(--d-panel-2);
  color: var(--d-text);
}

.docmd-item.is-active {
  background: var(--d-primary-soft);
  color: var(--d-text);
  font-weight: 500;
}

.docmd-external-glyph {
  margin-left: auto;
  font-size: 12px;
  opacity: 0.65;
}

.docmd-sidebar-footer {
  margin-top: auto;
  padding: 14px 20px 16px;
  border-top: 1px solid var(--d-border);
  color: var(--d-muted);
  font-size: 12px;
}

.docmd-sidebar-footer a {
  color: var(--d-muted);
}

.docmd-sidebar-footer a:hover {
  color: var(--d-text);
}

.docmd-overlay {
  display: none;
}

.docmd-main {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  min-width: 0;
}

.docmd-topbar {
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

.docmd-crumbs {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: var(--d-muted);
  font-size: 13px;
}

.docmd-crumb-sep {
  opacity: 0.5;
}

.docmd-crumb-current {
  overflow: hidden;
  color: var(--d-text);
  font-weight: 500;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.docmd-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.docmd-icon-btn {
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

.docmd-icon-btn:hover {
  background: var(--d-panel-2);
}

.docmd-menu-btn {
  display: none;
}

.docmd-content {
  flex: 1 0 auto;
  width: 100%;
  max-width: 860px;
  margin: 0 auto;
  padding: 40px 28px 96px;
}

.docmd-content > *:first-child {
  margin-top: 0;
}

.docmd-content h1,
.docmd-content h2,
.docmd-content h3,
.docmd-content h4,
.docmd-content h5,
.docmd-content h6 {
  margin: 36px 0 12px;
  line-height: 1.25;
  letter-spacing: -0.02em;
}

.docmd-content h1 {
  margin-top: 0;
  font-size: 2rem;
}

.docmd-content h2 {
  padding-bottom: 8px;
  border-bottom: 1px solid var(--d-border);
  font-size: 1.35rem;
}

.docmd-content h3 {
  font-size: 1.12rem;
}

.docmd-content h4 {
  font-size: 1rem;
}

.docmd-content p,
.docmd-content ul,
.docmd-content ol,
.docmd-content .docmd-table-wrap,
.docmd-content pre,
.docmd-content blockquote,
.docmd-content details {
  margin: 0 0 16px;
}

.docmd-content ul,
.docmd-content ol {
  padding-left: 24px;
}

.docmd-content li + li {
  margin-top: 4px;
}

.docmd-content li:has(> input[type="checkbox"]) {
  list-style: none;
  margin-left: -1.4em;
}

.docmd-content input[type="checkbox"] {
  margin-right: 8px;
  vertical-align: middle;
}

.docmd-content a {
  color: var(--d-primary);
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 3px;
}

.docmd-content a:hover {
  text-decoration-thickness: 2px;
}

.docmd-content strong {
  color: var(--d-text);
  font-weight: 600;
}

.docmd-content code {
  padding: 2px 6px;
  border: 1px solid var(--d-border);
  border-radius: 7px;
  background: var(--d-panel-2);
  font-family: var(--d-mono);
  font-size: 0.85em;
}

.docmd-content pre {
  overflow: auto;
  padding: 14px 16px;
  border: 1px solid var(--d-border);
  border-radius: var(--d-radius);
  background: var(--d-panel);
}

.docmd-content pre code {
  padding: 0;
  border: 0;
  border-radius: 0;
  background: none;
  font-size: 13px;
  line-height: 1.6;
}

.docmd-code {
  position: relative;
  margin: 0 0 16px;
}

.docmd-code pre {
  margin: 0;
}

.docmd-copy-btn {
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

.docmd-copy-btn:hover {
  border-color: var(--d-primary);
  color: var(--d-text);
}

.docmd-copy-btn.is-copied {
  border-color: var(--d-primary);
  color: var(--d-primary);
}

.docmd-content .hljs-comment,
.docmd-content .hljs-quote {
  color: var(--d-muted);
  font-style: italic;
}

.docmd-content .hljs-keyword,
.docmd-content .hljs-selector-tag,
.docmd-content .hljs-literal,
.docmd-content .hljs-section,
.docmd-content .hljs-doctag,
.docmd-content .hljs-operator {
  color: var(--d-primary);
}

.docmd-content .hljs-string,
.docmd-content .hljs-regexp,
.docmd-content .hljs-char.escape_,
.docmd-content .hljs-subst,
.docmd-content .hljs-symbol,
.docmd-content .hljs-bullet,
.docmd-content .hljs-addition {
  color: var(--d-code-string);
}

.docmd-content .hljs-number,
.docmd-content .hljs-variable,
.docmd-content .hljs-template-variable,
.docmd-content .hljs-attr,
.docmd-content .hljs-attribute,
.docmd-content .hljs-selector-attr,
.docmd-content .hljs-selector-pseudo,
.docmd-content .hljs-property {
  color: var(--d-code-number);
}

.docmd-content .hljs-title,
.docmd-content .hljs-built_in,
.docmd-content .hljs-type,
.docmd-content .hljs-class .hljs-title,
.docmd-content .hljs-function .hljs-title {
  color: var(--d-code-function);
}

.docmd-content .hljs-tag,
.docmd-content .hljs-name,
.docmd-content .hljs-selector-id,
.docmd-content .hljs-selector-class,
.docmd-content .hljs-template-tag,
.docmd-content .hljs-deletion,
.docmd-content .hljs-meta {
  color: var(--d-code-tag);
}

.docmd-content .hljs-emphasis {
  font-style: italic;
}

.docmd-content .hljs-strong {
  font-weight: 600;
}

.docmd-content .hljs-link {
  text-decoration: underline;
}

.docmd-content blockquote {
  margin-left: 0;
  padding: 2px 0 2px 16px;
  border-left: 2px solid var(--d-primary);
  color: var(--d-muted);
}

.docmd-content blockquote > *:last-child {
  margin-bottom: 0;
}

.docmd-content hr {
  margin: 32px 0;
  border: 0;
  border-top: 1px solid var(--d-border);
}

.docmd-content img {
  max-width: 100%;
  border-radius: var(--d-radius);
}

.docmd-table-wrap {
  overflow-x: auto;
  border: 1px solid var(--d-border);
  border-radius: var(--d-radius);
}

.docmd-content table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 14px;
}

.docmd-content th,
.docmd-content td {
  padding: 9px 14px;
  border-bottom: 1px solid var(--d-border);
  border-left: 1px solid var(--d-border);
  text-align: left;
}

.docmd-content th:first-child,
.docmd-content td:first-child {
  border-left: 0;
}

.docmd-content tr:last-child td {
  border-bottom: 0;
}

.docmd-content th {
  background: var(--d-panel-2);
  font-weight: 600;
}

.docmd-pager {
  display: flex;
  gap: 12px;
  margin-top: 56px;
  padding-top: 24px;
  border-top: 1px solid var(--d-border);
}

.docmd-pager-link {
  flex: 1 1 0;
  min-width: 0;
  padding: 12px 16px;
  border: 1px solid var(--d-border);
  border-radius: var(--d-radius);
  background: var(--d-panel);
}

.docmd-pager-link:hover {
  border-color: var(--d-primary);
}

.docmd-pager-link.is-next {
  text-align: right;
}

.docmd-pager-label {
  display: block;
  margin-bottom: 2px;
  color: var(--d-muted);
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.docmd-pager-name {
  display: block;
  overflow: hidden;
  color: var(--d-text);
  font-size: 14px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.docmd-state {
  padding: 56px 0;
  color: var(--d-muted);
  font-size: 14px;
}

.docmd-state strong {
  display: block;
  margin-bottom: 6px;
  color: var(--d-text);
  font-size: 15px;
}

.docmd-state p {
  margin: 0 0 8px;
}

.docmd-state code {
  padding: 2px 6px;
  border: 1px solid var(--d-border);
  border-radius: 7px;
  background: var(--d-panel-2);
  font-family: var(--d-mono);
  font-size: 12.5px;
}

.docmd-skeleton {
  padding-top: 4px;
}

.docmd-skeleton-line,
.docmd-skeleton-block {
  background: var(--d-panel);
  background: linear-gradient(90deg, var(--d-panel) 25%, var(--d-panel-2) 50%, var(--d-panel) 75%);
  background-size: 200% 100%;
  border-radius: var(--d-radius);
  animation: docmd-shimmer 1.4s linear infinite;
}

.docmd-skeleton-line {
  height: 12px;
  margin-bottom: 14px;
}

.docmd-skeleton-title {
  width: 42%;
  height: 26px;
  margin-bottom: 30px;
}

.docmd-skeleton-line:nth-of-type(2) {
  width: 96%;
}

.docmd-skeleton-line:nth-of-type(3) {
  width: 88%;
}

.docmd-skeleton-line:nth-of-type(4) {
  width: 94%;
}

.docmd-skeleton-line:nth-of-type(5) {
  width: 64%;
}

.docmd-skeleton-block {
  height: 128px;
  margin: 26px 0;
}

.docmd-skeleton-line:nth-of-type(7) {
  width: 90%;
}

.docmd-skeleton-line:nth-of-type(8) {
  width: 97%;
}

.docmd-skeleton-line:nth-of-type(9) {
  width: 70%;
  margin-bottom: 0;
}

@keyframes docmd-shimmer {
  from {
    background-position: 200% 0;
  }

  to {
    background-position: -200% 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .docmd-skeleton-line,
  .docmd-skeleton-block {
    animation: none;
  }
}

@media (max-width: 900px) {
  .docmd-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    width: 280px;
    transform: translateX(-100%);
    transition: transform 0.18s ease;
  }

  .docmd.is-open .docmd-sidebar {
    transform: none;
  }

  .docmd-overlay {
    position: fixed;
    inset: 0;
    z-index: 15;
    display: none;
    background: rgba(0, 0, 0, 0.5);
  }

  .docmd.is-open .docmd-overlay {
    display: block;
  }

  .docmd-menu-btn {
    display: grid;
  }

  .docmd-content {
    padding: 28px 18px 72px;
  }

  .docmd-content h1 {
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
    token: 0
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
    if (document.getElementById("docmd-styles")) return;
    var links = document.querySelectorAll('link[rel="stylesheet"]');
    for (var i = 0; i < links.length; i++) {
      var href = links[i].getAttribute("href") || "";
      if (/(^|\/)docmd(\.min)?\.css(\?|#|$)/.test(href)) return;
    }
    var style = document.createElement("style");
    style.id = "docmd-styles";
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
          throw new Error("DocMD could not load the Markdown parser from " + MARKED_URL);
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
      if (parent && parent.classList && parent.classList.contains("docmd-table-wrap")) continue;
      var wrapper = document.createElement("div");
      wrapper.className = "docmd-table-wrap";
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
      if (parent && parent.classList && parent.classList.contains("docmd-code")) continue;
      var wrapper = document.createElement("div");
      wrapper.className = "docmd-code";
      parent.insertBefore(wrapper, pre);
      wrapper.appendChild(pre);
      var button = document.createElement("button");
      button.type = "button";
      button.className = "docmd-copy-btn";
      button.textContent = "Copy";
      button.setAttribute("aria-label", "Copy code");
      wrapper.appendChild(button);
    }
  }

  function copyClick(event) {
    var button = event.target.closest ? event.target.closest(".docmd-copy-btn") : null;
    if (!button) return;
    var wrapper = button.closest(".docmd-code");
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
      items = Array.isArray(raw.sections) ? raw.sections : Array.isArray(raw.items) ? raw.items : [];
      if (raw.base_url || raw.baseUrl) {
        var base = String(raw.base_url || raw.baseUrl);
        if (base.charAt(base.length - 1) !== "/") base += "/";
        baseUrl = resolveUrl(baseUrl, base);
      }
    }
    if (!meta.name) meta.name = "Documentation";

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
    return document.getElementById("docmd") || document.body;
  }

  function buildShell(root, config, theme) {
    root.classList.add("docmd");
    root.setAttribute("data-docmd-theme", theme);
    root.innerHTML =
      '<aside class="docmd-sidebar">' +
      '<div class="docmd-brand"><span class="docmd-brand-mark">M</span><span class="docmd-brand-name"></span></div>' +
      '<div class="docmd-search"><input type="search" class="docmd-search-input" placeholder="Search…" aria-label="Search pages"></div>' +
      '<nav class="docmd-nav"></nav>' +
      '<div class="docmd-search-empty" hidden>No results</div>' +
      '<div class="docmd-sidebar-footer"><a href="https://github.com/alesis-buzz/docmd" target="_blank" rel="noopener noreferrer">Powered by docmd</a></div>' +
      "</aside>" +
      '<div class="docmd-overlay"></div>' +
      '<div class="docmd-main">' +
      '<header class="docmd-topbar">' +
      '<button class="docmd-icon-btn docmd-menu-btn" type="button" aria-label="Toggle navigation">☰</button>' +
      '<div class="docmd-crumbs"></div>' +
      '<div class="docmd-actions">' +
      '<button class="docmd-icon-btn docmd-theme-btn" type="button"></button>' +
      "</div>" +
      "</header>" +
      '<main class="docmd-content"></main>' +
      "</div>";

    var brandMark = root.querySelector(".docmd-brand-mark");
    brandMark.textContent = config.name.charAt(0).toUpperCase();
    root.querySelector(".docmd-brand-name").textContent = config.name;
    root.querySelector(".docmd-brand").addEventListener("click", function () {
      if (config.pages[0]) go(config.pages[0].slug);
    });
    state.nav = root.querySelector(".docmd-nav");
    state.search = root.querySelector(".docmd-search-input");
    state.searchEmpty = root.querySelector(".docmd-search-empty");
    state.content = root.querySelector(".docmd-content");
    state.crumbs = root.querySelector(".docmd-crumbs");
    state.nav.appendChild(buildNav(config.sections));
    state.search.addEventListener("input", filterNav);
    state.content.addEventListener("click", copyClick);

    root.querySelector(".docmd-theme-btn").addEventListener("click", function () {
      applyTheme(state.theme === "dark" ? "light" : "dark");
    });
    root.querySelector(".docmd-menu-btn").addEventListener("click", function () {
      root.classList.toggle("is-open");
    });
    root.querySelector(".docmd-overlay").addEventListener("click", function () {
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
        section.className = "docmd-section";
        var title = document.createElement("div");
        title.className = "docmd-section-title";
        title.textContent = item.name;
        title.dataset.name = normalizeText(item.name);
        section.appendChild(title);
        section.appendChild(buildNav(item.children));
        fragment.appendChild(section);
        return;
      }
      var link = document.createElement("a");
      link.className = "docmd-item";
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
        glyph.className = "docmd-external-glyph";
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

    function matches(name) {
      if (!name) return false;
      for (var i = 0; i < terms.length; i++) {
        if (name.indexOf(terms[i]) === -1) return false;
      }
      return true;
    }

    function walk(section, ancestorMatch) {
      var title = section.querySelector(":scope > .docmd-section-title");
      var titleMatch = ancestorMatch || (!!title && matches(title.dataset.name));
      var visibleChildren = 0;
      var children = section.children;
      for (var i = 0; i < children.length; i++) {
        var child = children[i];
        if (child.classList.contains("docmd-section")) {
          var sectionVisible = walk(child, titleMatch);
          child.hidden = !sectionVisible;
          if (sectionVisible) visibleChildren++;
        } else if (child.classList.contains("docmd-item")) {
          var itemVisible = all || titleMatch || matches(child.dataset.name);
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
      if (!section.classList.contains("docmd-section")) continue;
      var visible = walk(section, false);
      section.hidden = !visible;
      if (visible) visibleSections++;
    }
    state.searchEmpty.hidden = visibleSections > 0;
  }

  function applyTheme(theme) {
    state.theme = theme === "light" ? "light" : "dark";
    if (state.root) state.root.setAttribute("data-docmd-theme", state.theme);
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
    var button = state.root.querySelector(".docmd-theme-btn");
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
        separator.className = "docmd-crumb-sep";
        separator.textContent = "·";
        state.crumbs.appendChild(separator);
      }
      var span = document.createElement("span");
      span.textContent = part;
      if (index === parts.length - 1) span.className = "docmd-crumb-current";
      state.crumbs.appendChild(span);
    });
  }

  function markActive(slug) {
    var items = state.nav.querySelectorAll(".docmd-item[data-slug]");
    for (var i = 0; i < items.length; i++) {
      items[i].classList.toggle("is-active", items[i].dataset.slug === slug);
    }
  }

  function buildPager(page) {
    var pager = document.createElement("nav");
    pager.className = "docmd-pager";
    var previous = state.config.pages[page.index - 1];
    var next = state.config.pages[page.index + 1];
    [previous ? { page: previous, label: "Previous" } : null, next ? { page: next, label: "Next", forward: true } : null]
      .filter(Boolean)
      .forEach(function (entry) {
        var link = document.createElement("a");
        link.className = "docmd-pager-link" + (entry.forward ? " is-next" : "");
        link.href = "#/" + entry.page.slug;
        var label = document.createElement("span");
        label.className = "docmd-pager-label";
        label.textContent = entry.label;
        var name = document.createElement("span");
        name.className = "docmd-pager-name";
        name.textContent = entry.page.name;
        link.appendChild(label);
        link.appendChild(name);
        pager.appendChild(link);
      });
    return pager.children.length ? pager : null;
  }

  function stateMessage(title, detail, hint) {
    var html = '<div class="docmd-state"><strong>' + escapeHtml(title) + "</strong>";
    if (detail) html += "<p>" + escapeHtml(detail) + "</p>";
    if (hint) html += "<p><code>" + escapeHtml(hint) + "</code></p>";
    return html + "</div>";
  }

  function skeletonHtml() {
    var line = '<div class="docmd-skeleton-line"></div>';
    return (
      '<div class="docmd-skeleton" role="status" aria-label="Loading page">' +
      '<div class="docmd-skeleton-line docmd-skeleton-title"></div>' +
      line +
      line +
      line +
      line +
      '<div class="docmd-skeleton-block"></div>' +
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
          '<article class="docmd-article">' + sanitize(result.marked.parse(result.markdown, { gfm: true })) + "</article>";
        var article = state.content.querySelector(".docmd-article");
        if (article) {
          decorateTables(article);
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
    root.classList.add("docmd");
    if (!root.getAttribute("data-docmd-theme")) root.setAttribute("data-docmd-theme", state.theme);
    root.innerHTML =
      '<div class="docmd-main"><main class="docmd-content">' +
      stateMessage("DocMD could not start", error && error.message ? error.message : String(error)) +
      "</main></div>";
  }

  function InitDocs(input, options) {
    options = options || {};
    state.options = options;
    ensureStyles();
    var root = resolveRoot(options);
    state.root = root;
    var initialTheme = storedTheme() || options.theme || "dark";
    root.setAttribute("data-docmd-theme", initialTheme === "light" ? "light" : "dark");

    return loadConfig(input)
      .then(function (loaded) {
        var config = normalize(loaded.raw, loaded.baseUrl);
        state.config = config;
        state.theme = initialTheme === "light" ? "light" : "dark";
        if (config.theme && !storedTheme() && !options.theme) state.theme = config.theme;
        buildShell(root, config, state.theme);
        applyPrimary(options.primary || config.primary);
        state.content.addEventListener("click", contentClick);
        window.addEventListener("hashchange", onHashChange);
        var slug = slugFromHash() || (config.pages[0] && config.pages[0].slug);
        if (slug) showPage(slug);
        else state.content.innerHTML = stateMessage("Nothing to show", "This configuration has no pages.");
        return api;
      })
      .catch(function (error) {
        if (!state.config) fatal(root, error);
        throw error;
      });
  }

  function autoInit() {
    var scripts = document.querySelectorAll("script[data-docmd]");
    for (var i = 0; i < scripts.length; i++) {
      var script = scripts[i];
      var input = script.getAttribute("data-docmd");
      if (!input) continue;
      InitDocs(input, {
        target: script.getAttribute("data-target") || null,
        primary: script.getAttribute("data-primary") || null,
        theme: script.getAttribute("data-theme") || null,
        highlight: script.getAttribute("data-highlight") === "false" ? false : null,
        copy: script.getAttribute("data-copy") === "false" ? false : null
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
