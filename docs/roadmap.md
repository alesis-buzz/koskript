# Roadmap

Koskript is in early development. This page tracks what is done, what is next,
and the known limitations.

## Done

- Dynamic typing: `int`, `float`, `string`, `bool`, `null`, `array`, `map`
- `local` / `const` with block-level **lexical scoping** and closures
- Functions, recursion and lambda expressions
- `if` / `elseif` / `else`
- `while`, `for`, `foreach` loops with `break` / `continue`
- Member access and index access
- Classes: inheritance, visibility, static methods, constructors, `super`
- Python interop: values, callables, objects and classes (dunder attributes are blocked)
- [Standard library](standard-library.md): core builtins plus `map`, `array`, `string`, `math` and `json`
- Compiled execution engine (AST to Python code) with lexical slot resolution
- PyPI package

## Next

- `try` / `catch` / `throw`. Today any script error aborts the whole
  `execute()` call.
- Runtime error locations: include line and column in runtime errors (syntax
  errors already have them).
- Index assignment (`items[0] = 9`) and compound assignment (`+=`, `-=`, `*=`,
  `/=`, `%=`).
- Module imports (`import "mymodule"`).
- Wrap host exceptions raised while evaluating (for example `ZeroDivisionError`)
  as `Errors.RuntimeError`.
- Fix the newline/call chaining ambiguity: a line starting with `(` after a call
  is parsed as a chained call.
- A CI pipeline running the committed test suite.

## Later

- More operators: `**`, bitwise (`&`, `|`, `^`, `<<`, `>>`) and ternary `?:`.
- `in` membership expression (the keyword is reserved but there is no operator).
- Richer classes: interfaces/abstract methods, static fields, getters/properties.
- String interpolation.
- Standard library growth: `time`, `os`, iterators and streams.
- A bytecode VM and a custom parser to replace Lark.

## Performance

Koskript compiles the AST into Python functions instead of walking the tree:
statements become real Python loops/branches, expressions are inlined, and
every lexical scope is resolved to numeric slots. Compared to the original
tree-walking interpreter this is roughly **8-30x faster** depending on the
workload; on `benchmark.py` the interpreter now runs between **4x and 24x**
slower than equivalent CPython code (it used to be 90-200x).

Remaining hot spots are object/class heavy code (member access, method
dispatch), so the work plan is: inline caches for member access, a custom
parser to replace Lark, and a bytecode VM in the long term.
