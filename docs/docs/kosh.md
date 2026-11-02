# Koskript Headers (`.kosh`)

`.kosh` files are **editor/tooling headers only**. They are not part of the
Koskript language runtime and are **never executed** by `KoskriptRuntime`.

## Purpose

Headers exist to support IDE features (autocompletion, diagnostics, hover) in
the VSCode extension. They describe the shape of functions, classes and
constants without providing implementations.

## What you can define

- Functions:
  ```koskript
  fun add(a, b)
  ```
- Classes and methods:
  ```koskript
  class Point {
      public fun x()
      public fun move(dx, dy)
  }
  ```
- Constants:
  ```koskript
  const PI = 3.14
  ```
- Namespaces:
  ```koskript
  namespace Utils {
      fun double(x)
  }
  ```
- Imports:
  ```koskript
  import "math.kosh" as math
  ```

## Properties

- Bodies are **optional**: `fun name(params)` is valid.
- Only declarations are allowed; no executable statements.
- Headers are parsed by the LSP and indexed for autocompletion.
- `.kosh` files are not loaded by `import` in Koskript scripts.

## Do they execute?

No. `.kosh` files are never compiled or executed. They only provide metadata
for tooling.