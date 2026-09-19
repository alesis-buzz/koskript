![Koskript](https://raw.githubusercontent.com/alesisce/koskript/refs/heads/main/banner.png)

# Koskript

Koskript is a simple, embeddable, and lightweight scripting language designed to be used as a DSL inside Python applications. It features dynamic typing, lexical scoping, and native Python interop — letting you expose any Python function or object directly to your scripts.

> **NOTE:** Koskript is currently in early development. Features like module imports, more types, and performance improvements are on the way.

---

## Features

- Dynamic typing.
- Block-level lexical scoping with `local` declarations
- Native Python interop via `KoskriptObject`
- `if`, `elseif`, `else`
- `while`, `for`, `foreach` loops with `break` / `continue`
- Member access — `map.key.subkey`
- Index access — `array[0]`, `map["key"]`
- First-class functions and lambda expressions
- Arithmetic (`+`, `-`, `*`, `/`, `%`), comparison and logical operators
- Embeddable in any Python application

---

## Installation

Clone the repository and import it directly into your project:

```bash
git clone https://github.com/alesisce/koskript.git
```

> PyPI package coming soon.

---

## Quick Start

```python
from koskript import KoskriptRuntime

runtime = KoskriptRuntime({
    "print": print
})
runtime.execute("""
local x = 10
local y = 26

print(x+y)
""")
```

Any Python value or callable you pass in is wrapped automatically — no need to build `KoskriptObject` yourself.

---

## Example

```koskript
// Student grade checker
local students = {
    "Aleix": {
        "age": 17,
        "grade": 95
    },
    "Maria": {
        "age": 15,
        "grade": 72
    },
    "Juan": {
        "age": 18,
        "grade": 88
    }
}

local passing_grade = 75
                   
foreach (name, data in students) {
    local grade = data.grade

    if (grade >= passing_grade) {
        print("PASS:", name, "->", grade) // Depends on how you implement it.
    } elseif (grade >= 60) {
        print("NEAR PASS:", name, "->", grade)
    } else {
        print("FAIL:", name, "->", grade)
    }
}
```

Output:
```
PASS: Aleix -> 95
NEAR PASS: Maria -> 72
PASS: Juan -> 88
```

---

## Language Reference

### Types

| Type | Description |
|------|-------------|
| `int` | Integer number |
| `float` | Floating-point number |
| `string` | Text string |
| `bool` | `true` or `false` |
| `null` | The absence of a value |
| `array` | Ordered list |
| `map` | Key-value store |

### Variables

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

Variables declared with `local` are scoped to the block they are declared in — including `if`, `while`, `for` and `foreach` bodies.

### Functions

```koskript
fn add(a, b) {
    return a + b
}

local result = add(10, 20)
```

### Operators

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

### Control Flow

```koskript
if (x > 10) {
    print("big")
} elseif (x == 10) {
    print("exact")
} else {
    print("small")
}
```

### Lambda Functions

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

### Loops

```koskript
// while
while (x > 0) {
    x = x - 1
}

// for — iterate array
for (item in items) {
    print(item)
}

// foreach — iterate map
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

### Member Access

```koskript
local user = { "name": "Aleix", "age": 17 }
print(user.name)
print(user.age)
```

### Index Access

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

### Strings

Strings support single or double quotes and the escapes `\n`, `\t`, `\r`, `\0`, `\\`, `\"` and `\'`:

```koskript
print("line one\nline two")
```

### Comments

```koskript
// line comments start with two slashes
```

### Reserved Keywords

The following words cannot be used as identifiers:

`if` `elseif` `else` `while` `for` `foreach` `fn` `return` `local` `true` `false` `null` `and` `or` `not` `in` `break` `continue`

### Python Interop

Any Python value or callable can be exposed to Koskript. They are wrapped in a `KoskriptObject` automatically:

```python
from koskript import KoskriptRuntime

runtime = KoskriptRuntime({
    "print": print,
    "len": len,
})

# add more later — register() is chainable
runtime.register("sqrt", math.sqrt)
runtime["now"] = time.time
```

### Embedding API

`execute()` returns the value of the last evaluated expression, or the value of a top-level `return`:

```python
runtime = KoskriptRuntime({"print": print})
result = runtime.execute("local x = 10\nx * 2")   # 20
result = runtime.execute("return 1 + 2")           # 3
```

For a quick one-off script, use the `run()` helper:

```python
from koskript import run

run("print(1 + 2)", print=print)   # 3
```

Errors raised by scripts are available under `koskript.Errors`:

```python
from koskript import Errors

try:
    runtime.execute("local a = [1]\nprint(a[5])")
except Errors.RuntimeError as e:
    print(e)
```

---

## Roadmap

- [x] Index access (`array[0]`, `map["key"]`)
- [x] `float` type
- [x] `null` type
- [x] `break` / `continue` statements
- [ ] Module imports (`import "mymodule"`)
- [ ] Performance improvements
- [ ] Standard library
- [ ] PyPI package
- [ ] Custom parser (remove Lark dependency)
- [ ] VM-based execution

---

## License

Koskript is licensed under the Mozilla Public License 2.0 (MPL-2.0).

You are free to use, modify, and redistribute Koskript. However, you may not redistribute this project under a different name or claim authorship of the Koskript language.

**Koskript is a trademark of Alesis.**

---

*Built with ❤️ by Alesis*
