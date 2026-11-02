"""A minimal Language Server for Koskript (JSON-RPC over stdio)."""

import json
import sys
import threading

from .lang.parser import parse
from .lang import emtypes
from .stdlib.core import build as build_core
from .headers import _collect


KEYWORDS = [
    "let", "const", "fun", "wrapper", "class", "extends", "namespace",
    "error", "import", "as", "if", "elseif", "else", "while", "for",
    "foreach", "return", "break", "continue", "throw", "try", "catch",
    "finally", "static", "public", "private", "this", "super", "new",
    "true", "false", "null", "and", "or", "not", "in",
]

BUILTINS = list(build_core().keys())


def read_message():
    headers = {}
    while True:
        line = sys.stdin.readline()
        if not line:
            return None
        line = line.strip("\r\n")
        if line == "":
            break
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()
    length = int(headers.get("content-length", 0))
    if length == 0:
        return None
    body = sys.stdin.read(length)
    return json.loads(body)


def send_message(message):
    body = json.dumps(message, ensure_ascii=False)
    data = body.encode("utf-8")
    sys.stdout.write(f"Content-Length: {len(data)}\r\n\r\n")
    sys.stdout.buffer.write(data)
    sys.stdout.flush()


class DocumentStore:
    def __init__(self):
        self.docs = {}

    def update(self, uri, text):
        self.docs[uri] = text

    def get(self, uri):
        return self.docs.get(uri, "")


def collect_symbols(code):
    symbols = {"functions": [], "classes": [], "constants": []}
    try:
        statements = parse(code)
    except Exception:
        return symbols
    # reuse header collector by wrapping statements
    fake = {"functions": [], "classes": [], "constants": [], "namespaces": []}

    def collect(stmts, target):
        for stmt in stmts:
            kind = type(stmt)
            if kind is emtypes.FnDef:
                target["functions"].append(stmt.name)
            elif kind is emtypes.ClassDef:
                target["classes"].append(stmt.name)
                for m in stmt.methods:
                    target["functions"].append(f"{stmt.name}.{m.name}")
            elif kind is emtypes.ConstDecl or kind is emtypes.LocalDecl:
                target["constants"].append(stmt.name)
            elif kind is emtypes.NamespaceDef:
                nested = {"functions": [], "classes": [], "constants": [], "namespaces": []}
                collect(stmt.body, nested)
                for f in nested["functions"]:
                    target["functions"].append(f"{stmt.name}.{f}")
                target["classes"].extend(nested["classes"])
                target["constants"].extend(nested["constants"])

    collect(statements, fake)
    symbols["functions"] = fake["functions"]
    symbols["classes"] = fake["classes"]
    symbols["constants"] = fake["constants"]
    return symbols


def diagnostics_for(uri, text):
    items = []
    try:
        parse(text)
    except Exception as exc:
        message = str(exc)
        items.append({
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": 0, "character": 1},
            },
            "severity": 1,
            "source": "koskript",
            "message": message,
        })
    return items


def main():
    store = DocumentStore()
    running = True
    while running:
        msg = read_message()
        if msg is None:
            break
        method = msg.get("method")
        params = msg.get("params", {})
        msg_id = msg.get("id")

        if method == "initialize":
            send_message({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "capabilities": {
                        "textDocumentSync": 1,
                        "completionProvider": {"triggerCharacters": [".", ":"]},
                        "hoverProvider": False,
                        "documentSymbolProvider": True,
                    }
                },
            })
        elif method == "initialized":
            pass
        elif method == "shutdown":
            send_message({"jsonrpc": "2.0", "id": msg_id, "result": None})
        elif method == "exit":
            running = False
        elif method == "textDocument/didOpen":
            uri = params["textDocument"]["uri"]
            text = params["textDocument"]["text"]
            store.update(uri, text)
            send_message({
                "jsonrpc": "2.0",
                "method": "textDocument/publishDiagnostics",
                "params": {"uri": uri, "diagnostics": diagnostics_for(uri, text)},
            })
        elif method == "textDocument/didChange":
            uri = params["textDocument"]["uri"]
            changes = params.get("contentChanges", [])
            if changes:
                text = changes[-1].get("text", "")
                store.update(uri, text)
                send_message({
                    "jsonrpc": "2.0",
                    "method": "textDocument/publishDiagnostics",
                    "params": {"uri": uri, "diagnostics": diagnostics_for(uri, text)},
                })
        elif method == "textDocument/completion":
            uri = params["textDocument"]["uri"]
            text = store.get(uri)
            symbols = collect_symbols(text)
            items = []
            for kw in KEYWORDS:
                items.append({"label": kw, "kind": 14})
            for b in BUILTINS:
                items.append({"label": b, "kind": 3})
            for f in symbols["functions"]:
                items.append({"label": f, "kind": 3})
            for c in symbols["classes"]:
                items.append({"label": c, "kind": 7})
            for v in symbols["constants"]:
                items.append({"label": v, "kind": 6})
            send_message({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": items,
            })
        elif method == "textDocument/documentSymbol":
            uri = params["textDocument"]["uri"]
            text = store.get(uri)
            symbols = collect_symbols(text)
            items = []
            for f in symbols["functions"]:
                items.append({"name": f, "kind": 12, "range": _empty_range(), "selectionRange": _empty_range()})
            for c in symbols["classes"]:
                items.append({"name": c, "kind": 5, "range": _empty_range(), "selectionRange": _empty_range()})
            send_message({"jsonrpc": "2.0", "id": msg_id, "result": items})
        else:
            if msg_id is not None:
                send_message({"jsonrpc": "2.0", "id": msg_id, "result": None})


def _empty_range():
    return {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 0}}


if __name__ == "__main__":
    main()