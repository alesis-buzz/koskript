![Koskript](https://raw.githubusercontent.com/alesisce/koskript/refs/heads/main/banner.png)

# Koskript

Koskript is a simple, embeddable, and lightweight scripting language for Python
applications. It features dynamic typing, lexical scoping, closures, classes and
native Python interop — letting you expose any Python function or object
directly to your scripts.

```python
from koskript import KoskriptRuntime

runtime = KoskriptRuntime()
runtime.execute("""
const names = ["Ana", "Luis"]
array.each(names, (name) { print("hello " + name) })
""")
```

> **NOTE:** Koskript is in early development. Module imports, error handling and
> performance improvements are on the way; expect the language and API to change
> between releases.

---

## Features

- Dynamic typing.
- Block-level lexical scoping with `local` declarations.
- Closures that capture their defining scope, including `this` inside methods.
- Constants with `const`.
- Classes with inheritance, visibility, static methods and constructors.
- Standard library: core builtins plus `map`, `array`, `string`, `math` and `json`.
- Native Python interop for functions, objects and classes.
- `if`, `elseif`, `else`.
- `while`, `for`, `foreach` loops with `break` / `continue`.
- Member access and index access.
- First-class functions and lambda expressions.
- Arithmetic, comparison and logical operators.
- Embeddable in any Python application.

---

## Installation

```bash
pip install -U koskript
```

Or clone the repository and import it directly:

```bash
git clone https://github.com/alesis-buzz/koskript.git
```

Koskript requires Python 3.10+ and [Lark](https://github.com/lark-parser/lark).

---

## Documentation

| Document | What it covers |
|---|---|
| [Getting started](docs/getting-started.md) | Installation, first script, a complete example |
| [Language reference](docs/language.md) | Types, variables, operators, control flow, functions, closures, loops, strings |
| [Classes](docs/classes.md) | Inheritance, visibility, static members, constructors, `super` |
| [Standard library](docs/standard-library.md) | Core builtins and the `map`, `array`, `string`, `math` and `json` namespaces |
| [Python interop](docs/python-interop.md) | Exposing Python values, callables and classes to scripts |
| [Embedding guide](docs/embedding.md) | `KoskriptRuntime`, `run()`, error handling and stdlib activation |
| [Roadmap](docs/roadmap.md) | What is done, what is planned, known limitations |

---

## License

Koskript is licensed under the Mozilla Public License 2.0 (MPL-2.0). See
[LICENSE](LICENSE) for the full text.

You are free to use, modify, and redistribute Koskript. However, you may not
redistribute this project under a different name or claim authorship of the
Koskript language.

**Koskript is a trademark of Alesis.**

---

*Built with ❤️ by Alesis*
