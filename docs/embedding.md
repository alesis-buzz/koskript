# Embedding Guide

Koskript runs inside your Python process. This guide covers the public API of
`KoskriptRuntime`.

## Creating a runtime

```python
from koskript import KoskriptRuntime

runtime = KoskriptRuntime()                       # standard library only
runtime = KoskriptRuntime({"print": print})       # stdlib + your globals
runtime = KoskriptRuntime(stdlib=False)           # nothing registered
```

Arguments:

| Argument | Meaning |
|---|---|
| `globals_map` | Mapping of names to Python values. Registered after the standard library, so it overrides it. |
| `stdlib` | `True` (default) registers the [standard library](standard-library.md). |

A runtime owns its interpreter state: globals, scopes and the standard library
namespaces. It is not thread-safe — create one runtime per thread or guard
access yourself.

## Executing code

`execute()` parses and runs a script. It returns the value of the last
evaluated expression, or the value of a top-level `return`:

```python
runtime = KoskriptRuntime()

result = runtime.execute("local x = 10\nx * 2")   # 20
result = runtime.execute("return 1 + 2")          # 3
```

The same runtime can execute multiple scripts; top-level declarations persist
between calls.

## Modules

`import "name"` inside a script loads a `.kos` file from the **process working
directory**:

```python
runtime.execute('import "utils"\nutils.hello()')
```

`execute_module()` runs a file as a module and returns it. Imports inside that
module resolve against the module's own directory, so `modules/app.kos` can
import `modules/helpers.kos` with `import "helpers"` no matter where the
process runs from:

```python
module = runtime.execute_module("modules/app.kos")

module.name        # "app"
module["run"]      # a Koskript function value
module.get("VERSION")
module.scope       # internal top-level scope
```

Modules are cached per runtime: executing the same file again returns the same
`Module`. A missing file raises `Errors.RuntimeError`; a circular import raises
`Errors.RuntimeError` too.

## One-shot scripts

`run()` keeps your process clean when you just need to evaluate a snippet:

```python
from koskript import run

run("print(1 + 2)")                # uses the standard library print
run("return 1 + 2")                # 3
run("len([1])", stdlib=False)      # Errors.NameError: 'len' is not defined
```

## Registering and reading values

```python
runtime = KoskriptRuntime()

runtime.register("double", lambda x: x * 2)
runtime.register_many({"triple": lambda x: x * 3})
runtime["quadruple"] = lambda x: x * 4

runtime["double"]        # Python function back on the host side
```

`register()` and `register_many()` return the runtime so calls can be chained.
Assigning with `runtime["name"] = value` is equivalent to `register`, and
registering a name that already exists replaces it.

## Error handling

Script errors are raised as exceptions under `koskript.Errors`:

| Exception | Raised when |
|---|---|
| `Errors.SyntaxError` | The script cannot be parsed. The message includes line, column and context. |
| `Errors.NameError` | A name is not defined. |
| `Errors.MismatchType` | A value has the wrong type (also used for wrong argument counts). |
| `Errors.ProtectedObject` | Code tries to reassign a `const`. |
| `Errors.RuntimeError` | Any other runtime failure (index out of range, invalid JSON...). |
| `Errors.KoskriptError` | A script `throw` reached the top level without a `catch`. |

`Errors.KoskriptError` carries the thrown error value in `e.instance`
(`e.instance.name` is the error type, `e.instance.message` its message, and
any extra fields live in `e.instance.fields`). Its own message is the error
name plus the message field. Errors caught by a script `try` block never
reach the host.

```python
from koskript import Errors

runtime = KoskriptRuntime()

try:
    runtime.execute("local a = [1]\nprint(a[5])")
except Errors.RuntimeError as e:
    print("script failed:", e)
```

Syntax errors are formatted with the offending line:

```python
try:
    runtime.execute("local = 1")
except Errors.SyntaxError as e:
    print(e)
# Syntax error at line 1, column 7:
# local = 1
#       ^
# Unexpected token...
```

## Installing the standard library manually

`build_globals()` returns a fresh dictionary containing the whole standard
library. Higher-order array functions (`map`, `filter`, `reduce`, `sort_by`,
`each`) need the runtime bridge that `KoskriptRuntime` provides automatically;
when installed by hand they raise `RuntimeError` if called.

```python
from koskript import KoskriptRuntime, build_globals

runtime = KoskriptRuntime(stdlib=False)
runtime.register_many(build_globals())
```

## Parsing only

If you need the raw tree or AST for tooling, the runtime exposes the Lark
grammar and the transformer as module-level objects:

```python
from koskript import grammar
from koskript.lang.astgen import KoskriptTransformer

tree = grammar.parse("1 + 2")
ast = KoskriptTransformer().transform(tree)
```

This is an internal API; it may change between releases.
