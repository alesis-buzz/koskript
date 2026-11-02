"""Helpers for reading Koskript header files (``.kosh``).

A ``.kosh`` file is a normal Koskript source that only contains
declarations: ``fun``, ``class``, ``const``, ``namespace`` and ``import``.
Bodies are usually empty (``{}``), so the file can be parsed with the
standard parser without being executed.
"""

from .lang.parser import parse
from .lang import emtypes


def _collect(statements, symbols):
    for stmt in statements:
        kind = type(stmt)
        if kind is emtypes.FnDef:
            symbols["functions"].append({
                "name": stmt.name,
                "params": list(stmt.params),
            })
        elif kind is emtypes.ClassDef:
            methods = []
            for method in stmt.methods:
                methods.append({
                    "name": method.name,
                    "params": list(method.params),
                    "modifiers": list(method.modifiers),
                })
            symbols["classes"].append({
                "name": stmt.name,
                "parent": stmt.parent_name,
                "methods": methods,
                "fields": [
                    {"name": f.name, "modifiers": list(f.modifiers)}
                    for f in stmt.fields
                ],
            })
        elif kind is emtypes.ConstDecl:
            symbols["constants"].append(stmt.name)
        elif kind is emtypes.NamespaceDef:
            nested = {"functions": [], "classes": [], "constants": [], "namespaces": []}
            _collect(stmt.body, nested)
            symbols["namespaces"].append({"name": stmt.name, "symbols": nested})


def load_header(source_or_path):
    """Parse a ``.kosh`` source or file path and return its symbol index."""
    if "\n" not in source_or_path and source_or_path.endswith(".kosh"):
        with open(source_or_path, "r", encoding="utf-8-sig") as handle:
            code = handle.read()
    else:
        code = source_or_path

    statements = parse(code)
    symbols = {"functions": [], "classes": [], "constants": [], "namespaces": []}
    _collect(statements, symbols)
    return symbols