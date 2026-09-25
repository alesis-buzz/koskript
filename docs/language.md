# Language Reference

## Types

| Type | Description |
|------|-------------|
| `int` | Integer number |
| `float` | Floating-point number |
| `string` | Text string |
| `bool` | `true` or `false` |
| `null` | The absence of a value |
| `array` | Ordered list |
| `map` | Key-value store |
| `function` | A declared function, a lambda or a bound method |
| `class` | A class object |
| `instance` | An instance of a class |
| `module` | A module loaded with `import` |

`type(value)` returns the name of a value's type as a string. Values coming
from Python report their Python type name instead.

## Variables

```koskript
local x = 10
local pi = 3.14
local name = "Koskript"
local active = true
local missing = null
local items = [1, 2, 3]
local empty = []
local config = { "debug": true, "version": 1 }
```

Variables declared with `local` are scoped to the block they are declared in —
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
fn make_counter() {
    local n = 0
    return () {
        n = n + 1
        return n
    }
}

const next = make_counter()
print(next())   // 1
print(next())   // 2

fn read_x() { return x }
fn caller() {
    local x = 5
    return read_x()   // error: 'x' is not defined
}
```

## Constants

`const` declares a read-only binding in the current scope. Reassigning it raises
a `ProtectedObject` error, but the contents of an `array` or `map` can still be
modified:

```koskript
const PI = 3.14
const CONFIG = { "debug": true }

CONFIG.debug = false   // ok, the binding is constant, not the contents

PI = 3.0               // error: cannot modify a constant value
```

## Functions

```koskript
fn add(a, b) {
    return a + b
}

local result = add(10, 20)
```

- `return` without a value exits the function returning `null`.
- Functions can call themselves (recursion works, including mutual recursion
  between top-level functions).
- Parameters are positional. Extra arguments are ignored and missing ones are
  bound to `null`.

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
- A module exposes its top-level `local`, `const`, `fn` and `class` names as
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

## Operators

```koskript
local a = 2 + 3 * 4      // 14  (precedence: * / % before + -)
local b = 10 % 3         // 1
local c = -a             // unary minus
local d = (a + b) * 2    // grouping with parentheses

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
    local x = 1 / 0
} catch e {
    print(e.name)      // ZeroDivisionError
    print(e.message)   // division by zero
}
```

## Lambda Functions

Lambdas are anonymous functions; the last expression is **not** returned
implicitly, use `return`:

```koskript
local greet = () {
    print("Hello world")
}

greet()

// lambdas can take parameters and return values
local add = (a, b) {
    return a + b
}

print(add(1, 2))

// invoke a lambda literal directly
print((() { return 42 })())
```

Lambdas and nested functions capture the scope where they are defined, so they
keep local state after the enclosing function returns (see
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
local user = { "name": "Aleix", "age": 17 }
print(user.name)
print(user.age)
```

Assignment to a map key uses the same syntax:

```koskript
user.age = 18
```

## Index Access

```koskript
local items = [10, 20, 30]
print(items[0])        // 10
print(items[-1])       // 30

local config = { "debug": true }
print(config["debug"]) // true

// member access and indexing can be chained
local data = { "nums": [1, 2, 3] }
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

## Truthiness

Conditions accept any value. `false`, `null`, `0`, `0.0`, `""`, `[]` and `{}`
are falsy; everything else is truthy. `bool(value)` applies the same rules.

## Comments

```koskript
// line comments start with two slashes
```

There are no block comments.

## Reserved Keywords

The following words cannot be used as identifiers:

`if` `elseif` `else` `while` `for` `foreach` `fn` `return` `local` `const`
`true` `false` `null` `and` `or` `not` `in` `break` `continue` `class`
`extends` `new` `static` `public` `private` `this` `super` `constructor`
`import` `as` `error` `throw` `try` `catch` `finally`

Because they are reserved, member names such as `array.foreach` are not
possible; the standard library uses `array.each` instead.

## Gotchas

Newlines are plain whitespace, so a line that starts with `(` after a previous
line ending in `)` is parsed as a **chained call**:

```koskript
local r = math.random()
local ok = (r >= 0) and (r < 1)   // fine: the line starts with `local`

// Avoid this:
// local r = math.random()
// (r >= 0) and (r < 1)           // parsed as math.random()(r >= 0) ...
```

Assign the expression to a variable first, or put the condition on the same
line as the call.
