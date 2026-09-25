# Koskript Documentation

Koskript is a small, embeddable scripting language for Python applications.
Scripts are parsed and executed by a `KoskriptRuntime`, and any Python value
you expose becomes available to them.

> **NOTE:** Koskript is in early development. The language and its API may
> still change between releases.

## Contents

| Document | What it covers |
|---|---|
| [Getting started](getting-started.md) | Installation, first script, a complete example |
| [Language reference](language.md) | Types, variables, operators, control flow, errors, functions, closures, modules, loops, strings |
| [Classes](classes.md) | Inheritance, visibility, static members, constructors, `super` |
| [Standard library](standard-library.md) | Core builtins and the `map`, `array`, `string`, `math` and `json` namespaces |
| [Python interop](python-interop.md) | Exposing Python values, callables and classes to scripts |
| [Embedding guide](embedding.md) | `KoskriptRuntime`, `run()`, error handling and stdlib activation |
| [Roadmap](roadmap.md) | What is done, what is planned, known limitations |

## Quick taste

```python
from koskript import KoskriptRuntime

runtime = KoskriptRuntime()
runtime.execute("""
const names = ["Ana", "Luis"]
array.each(names, (name) { print("hello " + name) })
""")
```

Output:

```
hello Ana
hello Luis
```

---

The documentation site is rendered with
[DocMD](https://github.com/alesis-buzz/docmd) (MIT), vendored in this folder.

