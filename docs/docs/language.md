# Language Reference

## Types

| Type | Description |
|------|-------------|
| `int` | Integer number |
| `float` | Floating-point number |
| `string` | Text string |
| `bytes` | Binary data |
| `bool` | `true` or `false` |
| `null` | The absence of a value |
| `array` | Ordered list |
| `map` | Key-value store |
| `function` | A declared function, a lambda or a bound method |
| `class` | A class object |
| `instance` | An instance of a class |
| `module` | A module loaded with `import` |
| `namespace` | A namespace declared with `namespace` |

`type(value)` returns the name of a value's type as a string. Values coming
from Python report their Python type name instead, except `bytes` and
`bytearray`, which report `bytes`.

## Variables

```koskript
let x = 10
let pi = 3.14
let name = "Koskript"
let active = true
let missing = null
let items = [1, 2, 3]
let empty = []
let config = { "debug"= true, "version"= 1 }
```

Variables declared with `let` are scoped to the block they are declared in —
including `if`, `while`, `for` and `foreach` bodies. A variable declared inside
a block is not visible after the block ends.

## Scoping

Koskript uses lexical scoping:

- A block sees the names of its enclosing blocks and the globals.
- Functions and lambdas capture the scope where they are **defined**, not where
  they are called.
- Assigning to a name (`x = value`) updates the nearest enclosing declaration.
  If no declaration exists, a `NameError` is raised.
- A function called by another function cannot see the caller's locals.

```koskript
fun make_counter() {
    let n = 0
    return () {
        n = n + 1
        return n
    }
}

const next = make_counter()
print(next())   // 1
print(next())   // 2

fun read_x() { return x }
fun caller() {
    let x = 5
    return read_x()   // error: 'x' is not defined
}
```

## Constants

`const` declares a read-only binding in the current scope. Reassigning it raises
a `ProtectedObject` error, but the contents of an `array` or `map` can still be
modified:

```koskript
const PI = 3.14
const CONFIG = { "debug"= true }

CONFIG.debug = false   // ok, the binding is constant, not the contents

PI = 3.0               // error: cannot modify a constant value
```

## Functions

```koskript
fun add(a, b) {
    return a + b
}

let result = add(10, 20)
```

- `return` without a value exits the function returning `null`.
- Functions can call themselves (recursion works, including mutual recursion
  between top-level functions).
- Parameters are positional. Extra arguments are ignored and missing ones are
  bound to `null`.

## Wrappers and Decorators

A `wrapper` is a function whose last expression is returned implicitly, so it
does not need a `return`. Wrappers are meant to be used as decorators:

```koskript
wrapper loud(target) {
    (name) {
        return target(name) + "!"
    }
}

@loud
fun greet(name) {
    return "hola " + name
}

print(greet("Ana"))   // hola Ana!
```

`@Decorator` wraps the `fun` or method written below it, like Python
decorators:

- `@Decorator` is `fun = Decorator(fun)`.
- `@Decorator(args)` is `fun = Decorator(args)(fun)`.
- Multiple decorators apply bottom-up: `@a @b fun f` is `a(b(f))`.
- Decorator expressions run once, when the definition executes.

They can decorate top-level `fun`, nested `fun` inside functions and methods,
and class methods:

```koskript
class Api {
    @loud
    public fun ping() { return "pong" }
}
```

The decorator receives the raw function as a normal value. For methods, that
value is the method itself: calling it inside a wrapper runs the original
implementation with the instance already bound, so `this` and `::Method()`
keep working — both in the method and in the wrapper:

```koskript
wrapper count_calls(target) {
    () {
        print("called")
        return target()
    }
}
```

Because a wrapper is just a function, it can also be called directly, stored
in variables and passed around:

```koskript
wrapper double(x) { x * 2 }

const times_two = double
print(times_two(21))   // 42
```

Only the last **expression** of a wrapper is returned implicitly; use `return`
for control flow and inside lambdas (see
[Lambda Functions](#lambda-functions)).

## Modules

`import` loads another `.kos` file as a module and binds it to a name:

```koskript
import "utils"          // binds `utils`
import "sub/math" as m  // binds `m`

print(utils.hello("Ana"))
print(m.double(21))
```

- The `.kos` extension is optional.
- The default binding is the file name without the extension. Use `as` to pick
  another name (also required when the file name is not a valid identifier).
- A module exposes its top-level `let`, `const`, `fun` and `class` names as
  members. `const` members are read-only; the other members can be read and
  updated and reflect the module's live state.
- Modules are loaded once per runtime and cached: importing the same file
  twice returns the same module object. Circular imports raise an error.
- Modules can use the standard library and any host globals registered in the
  runtime, and can import other modules.

Where imports are searched depends on how the code was started:

| Entry point | Imports resolve against |
|---|---|
| `KoskriptRuntime.execute()` | the current working directory of the Python process |
| `KoskriptRuntime.execute_module()` | the directory of the module file being executed |

Nested imports are always resolved against the directory of the module that
contains them, so a module in `modules/app.kos` can import its sibling with
`import "helpers"` regardless of the process working directory.

The host application can register extra search directories with
`runtime.add_import_path("dir")`; they are searched after the importer's own
directory, in the order they were added. See the
[Embedding guide](embedding.md#import-paths).

## Namespaces

A `namespace` groups declarations under a name so they can be organized without
creating a module:

```koskript
namespace Utils {
    const MAX = 3

    fun double(x) { return x * 2 }

    class Point {
        public x = 0
        constructor(x) { this.x = x }
    }
}

print(Utils.double(21))       // 42
print(Utils.MAX)              // 3
print(new Utils.Point(1).x)   // 1
```

- Namespaces can only contain declarations: `fun`, `wrapper`, `class`, `const`,
  `error`, `import` and nested namespaces.
- Members reference each other by short name and can also read the enclosing
  scope, including locals of the function that declares the namespace.
- Members are read-only from the outside: `Utils.MAX = 4` raises
  `ProtectedObject`.
- Namespaces can be nested: `App.Utils.double(2)`.
- The qualified forms `new Namespace.Class(...)` and
  `class Child extends Namespace.Base` work anywhere.
- `type(Utils)` is `"namespace"`.

## Operators

```koskript
let a = 2 + 3 * 4      // 14  (precedence: * / % before + -)
let b = 10 % 3         // 1
let c = -a             // unary minus
let d = (a + b) * 2    // grouping with parentheses

if (x >= 10 and not done or retry) {
    // ...
}
```

| Operators | Description |
|-----------|-------------|
| `+` `-` `*` `/` `%` | Arithmetic |
| `-x` | Unary minus |
| `==` `!=` `>` `<` `>=` `<=` | Comparison |
| `and` `or` `not` | Logical (short-circuiting) |
| `( )` | Grouping |

`+` is also used to concatenate strings.

## Control Flow

```koskript
if (x > 10) {
    print("big")
} elseif (x == 10) {
    print("exact")
} else {
    print("small")
}
```

## Errors

Errors are declared with `error`, raised with `throw` and handled with
`try` / `catch` / `finally`:

```koskript
error MyError (err) {
    err.message = "something went wrong"
}

try {
    throw MyError()
} catch e {
    print(e.name)      // MyError
    print(e.message)   // something went wrong
} finally {
    print("done")      // always runs
}
```

The first parameter of an error body is the error itself, so `err.message`
configures the message reported when the error is not caught. Extra
parameters become fields of the error:

```koskript
error HttpError (err, status) {
    err.message = "request failed"
    err.status = status
}

try {
    throw HttpError(404)
} catch e {
    print(e.status)    // 404
}
```

Only error values can be thrown. `catch` and `finally` are both optional and
can be combined; `finally` runs whether or not an error was thrown. The catch
variable lives in its own block scope, and `throw e` inside a `catch` rethrows
the error. Errors propagate out of functions and methods until some `try`
catches them; if none does, the script stops with an
`Errors.KoskriptError` whose message is the error name and its `message`.

Native Python failures raised by the runtime are caught too. Inside `catch`
they expose `e.name`, `e.message` and the original exception in `e.native`:

```koskript
try {
    let x = 1 / 0
} catch e {
    print(e.name)      // ZeroDivisionError
    print(e.message)   // division by zero
}
```

## Lambda Functions

Lambdas are anonymous functions; the last expression is **not** returned
implicitly, use `return`:

```koskript
let greet = () {
    print("Hello world")
}

greet()

// lambdas can take parameters and return values
let add = (a, b) {
    return a + b
}

print(add(1, 2))

// invoke a lambda literal directly
print((() { return 42 })())
```

Lambdas and nested functions capture the scope where they are defined, so they
keep let state after the enclosing function returns (see
[Scoping](#scoping)). Inside a method, closures also capture `this`, so they can
use fields, private members and `::Method()`.

## Classes

See the dedicated [Classes](classes.md) reference.

## Loops

```koskript
// while
while (x > 0) {
    x = x - 1
}

// for — iterate an array or any Python iterable (e.g. range())
for (item in items) {
    print(item)
}

// foreach — iterate a map
foreach (key, value in config) {
    print(key, value)
}
```

`break` exits the nearest loop and `continue` skips to the next iteration:

```koskript
for (item in items) {
    if (item == 2) {
        continue   // skip this item
    }
    if (item == 5) {
        break      // stop looping
    }
    print(item)
}
```

## Member Access

```koskript
let user = { "name": "Aleix", "age": 17 }
print(user.name)
print(user.age)
```

Assignment to a map key uses the same syntax:

```koskript
user.age = 18
```

On class instances the same `.` reads fields and calls methods
(`rex.speak()`), while `::` is reserved for instance methods: `::Method()`
inside a class, `instance::Method()` from outside and `super::Method()` for
the parent implementation. See [Dot vs double colon](classes.md#dot-vs-double-colon)
for the full comparison.

## Index Access

```koskript
let items = [10, 20, 30]
print(items[0])        // 10
print(items[-1])       // 30

let config = { "debug"= true }
print(config["debug"]) // true

// member access and indexing can be chained on the same line
let data = { "nums": [1, 2, 3] }
print(data.nums[1])    // 2
```

Reading is supported for arrays, maps, strings and Python objects with
`__getitem__`. Writing (`items[0] = 9`) is not supported yet; use
`array.insert`, `array.remove_at` and friends from the
[standard library](standard-library.md) to modify arrays.

## Strings

Strings support single or double quotes and the escapes `\n`, `\t`, `\r`,
`\0`, `\\`, `\"` and `\'`:

```koskript
print("line one\nline two")
```

There is no string interpolation yet; concatenate with `+` or use
`array.join` / `json.encode`.

## Bytes

`bytes` values hold binary data. Literals look like Python's, with a `b`
prefix before the quotes:

```koskript
let empty = b""
let text = b"Koskript"
let binary = b"\x00\x01\xff"

print(len(binary))     // 3
print(binary[2])       // 255
```

Inside a bytes literal the escapes `\n`, `\t`, `\r`, `\0`, `\\`, `\"` and
`\'` work like in strings, and `\xNN` inserts one arbitrary byte. Characters
outside ASCII are encoded as UTF-8, so `b"ñ"` is the two bytes `\xc3\xb1`.

- `+` concatenates two bytes values: `b"ab" + b"cd"` is `b"abcd"`.
- Comparisons (`==`, `!=`, `<`, `>`, ...) compare the byte sequences.
- `len(data)` is the number of bytes; `data[i]` returns the byte at `i` as an
  `int` between 0 and 255 (negative indexes are allowed).
- `for (byte in data)` iterates over those ints.
- `str(data)` renders the data as hexadecimal: `str(b"abc")` is `"0x616263"`.
  `print` uses the same form. `b""` renders as `"0x"`.

The [`bytes` namespace](standard-library.md#bytes) converts between bytes,
strings, hex strings and arrays of ints.

## Truthiness

Conditions accept any value. `false`, `null`, `0`, `0.0`, `""`, `b""`, `[]`
and `{}` are falsy; everything else is truthy. `bool(value)` applies the same
rules.

## Comments

```koskript
// line comments start with two slashes
```

There are no block comments.

## Reserved Keywords

The following words cannot be used as identifiers:

`if` `elseif` `else` `while` `for` `foreach` `fun` `wrapper` `return` `let`
`const` `true` `false` `null` `and` `or` `not` `in` `break` `continue` `class`
`extends` `new` `static` `public` `private` `this` `super` `constructor`
`import` `as` `error` `throw` `try` `catch` `finally` `namespace`

Because they are reserved, member names such as `array.foreach` are not
possible; the standard library uses `array.each` instead.

## Gotchas

Newlines are plain whitespace, with one exception: a line that **starts**
with `.`, `::`, `[` or `(` never continues the expression above it. A
postfix operator must stay on the same line as the expression it extends:

```koskript
let r = math.random()
(r >= 0) and (r < 1)   // two statements: the call, then the condition

let a = f(1)(2)      // same line: chained calls

let b = f(1)
[2]                    // two statements: the call, then an array
```

The rule looks at lines, not at syntax, so a line-start `(` or `[` has to be
a complete expression on its own. Inside a call's parentheses it can only
begin a new argument (right after a comma), so `f(a` followed by a line
starting with `(b))` is a syntax error: keep the call on one line or split
the arguments after the commas.

```koskript
let x = values.filter(
    (v) { return v > 0 },   // fine: the line starts a new argument
)
```

## Headers (`.kosh`)

`.kosh` files are **editor/tooling headers only**. They are not part of the
Koskript language runtime and are never executed by `KoskriptRuntime`. They
exist to support IDE features such as autocompletion and diagnostics in the
VSCode extension.

A `.kosh` file uses a lightweight subset of the Koskript syntax:

```koskript
fun add(a, b)
class Point {
    public fun x()
    public fun move(dx, dy)
}
const PI = 3.14
```

Function and method bodies are optional. The LSP scans `.kosh` files in the
same directory as the `.kos` file being edited and exposes their symbols.
