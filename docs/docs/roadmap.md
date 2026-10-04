# Roadmap

Koskript is in early development. This page tracks what is done, what is next,
and the known limitations.

## Done

- Dynamic typing: `int`, `float`, `string`, `bytes`, `bool`, `null`, `array`, `map`
- `local` / `const` with block-level **lexical scoping** and closures
- Functions, recursion and lambda expressions
- Wrappers with implicit return and Python-style decorators (`@wrapper`, `@wrapper(args)`) on functions and methods
- `if` / `elseif` / `else`
- `while`, `for`, `foreach` loops with `break` / `continue`
- Member access and index access
- Classes: inheritance, visibility, static methods, constructors, `super`
- `try` / `catch` / `finally` with `throw` and user-defined `error` types
- Module imports: `import "path"` with per-module resolution and caching
- Host import paths: `KoskriptRuntime.add_import_path()` searched after the importer's folder
- Namespaces: `namespace Name { ... }` with read-only members and qualified `new`/`extends`
- Python interop: values, callables, objects and classes (dunder attributes are blocked)
- [Standard library](standard-library.md): core builtins plus `map`, `array`, `string`, `bytes`, `math` and `json`
- Compiled execution engine (AST to Python code) with lexical slot resolution
- PyPI package

## Next

- Make the native parser the default. It is written and verified against the
  grammar, and it is already available behind
  `KoskriptRuntime(native_parser_experiment=True)`: no dependency, ~6x faster
  parsing and a ~8x faster start. The default is still Lark until it has been
  validated in production.
- Runtime error locations: include line and column in runtime errors (syntax
  errors already have them).
- Index assignment (`items[0] = 9`) and compound assignment (`+=`, `-=`, `*=`,
  `/=`, `%=`).
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
- A bytecode VM.

## Performance

Koskript compiles the AST into Python functions instead of walking the tree:
statements become real Python loops/branches, expressions are inlined, and
every lexical scope is resolved to numeric slots. Compared to the original
tree-walking interpreter this is roughly **8-30x faster** depending on the
workload; on `benchmark.py` the interpreter now runs between **4x and 17x**
slower than equivalent CPython code (it used to be 90-200x).

Remaining hot spots are the compiler (it turns the AST into Python code for
every function of every script) and object/class heavy code. The compiler work
already done:

- `return` is a real Python return instead of an exception, and a loop body
  without `break`/`continue` no longer pays for a `try` block on every
  iteration;
- a function that cannot leak its scope recycles the previous call's one
  instead of allocating a `Scope` per call;
- a runtime compiles each source once, so running the same script again skips
  parsing and compiling it.

On `examples/benchmark.kos` (620 lines) the execution went from 32 ms to
15 ms, and re-running the same source from 142 ms to 15 ms.

What is left: the generated source is 6x the size of the script and Python's
own `compile()` is now the single biggest phase, so the next wins are inline
caches for member access, emitting less code per name, and a bytecode VM in the
long term.

The front end has an experimental pure Python alternative: a hand written
scanner and recursive descent parser that reads the same grammar and builds the
same AST. It parses about **6x faster** than Lark's parse plus transform, and it
removes the LALR table build that used to run on every import. It is opt-in with
`KoskriptRuntime(native_parser_experiment=True)` until it replaces Lark as the
default.
