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
- A committed test suite and CI (tests currently live outside version control).

## Later

- More operators: `**`, bitwise (`&`, `|`, `^`, `<<`, `>>`) and ternary `?:`.
- `in` membership expression (the keyword is reserved but there is no operator).
- Richer classes: interfaces/abstract methods, static fields, getters/properties.
- String interpolation.
- Standard library growth: `time`, `os`, iterators and streams.
- A bytecode VM and a custom parser to replace Lark.

## Performance

Koskript walks an AST from Python, so it is roughly 90-200x slower than
equivalent CPython code depending on the workload. Function calls, member
access and object creation are the most expensive operations; parse time is
negligible compared to execution.

Work plan: interpreter micro-optimizations (scope handling and member access),
then a custom parser, and a bytecode VM in the long term.
