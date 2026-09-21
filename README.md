![Koskript](https://raw.githubusercontent.com/alesisce/koskript/refs/heads/main/banner.png)

# Koskript

Koskript is a simple, embeddable, and lightweight scripting language designed to be used as a DSL inside Python applications. It features dynamic typing, lexical scoping, and native Python interop — letting you expose any Python function or object directly to your scripts.

> **NOTE:** Koskript is currently in early development. Features like module imports, more types, and performance improvements are on the way.
> Koskript sadly is extremely slow, but we are working on fixing those problems.
---

## Features

- Dynamic typing.
- Block-level lexical scoping with `local` declarations
- Constants with `const`
- Classes with inheritance, visibility, static methods and constructors
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

or

```bash
pip install -U koskript
```

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

### Constants

`const` declares a read-only binding in the current scope. Reassigning it raises a `ProtectedObject` error, but the contents of an `array` or `map` can still be modified:

```koskript
const PI = 3.14
const CONFIG = { "debug": true }

CONFIG.debug = false   // ok, the binding is constant, not the contents

PI = 3.0               // error: cannot modify a constant value
```

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

Lambdas and nested functions capture the scope where they are defined, so they keep local state after the enclosing function returns:

```koskript
fn counter() {
    local n = 0
    return () {
        n = n + 1
        return n
    }
}

const next = counter()

print(next())   // 1
print(next())   // 2
```

Inside a method, closures also capture `this`, so they can use fields, private members and `::Method()`.

### Classes

Classes support single inheritance, visibility modifiers, static methods and constructors:

```koskript
class Animal {
    public name = "generic"     // fields can be public or private
    private energy = 100

    constructor(name) {
        this.name = name
    }

    public fn speak() {
        return "..."
    }

    public fn describe() {
        return ::speak() + " " + this.name   // :: calls an instance method
    }

    private fn drain() {
        this.energy = this.energy - 10
    }

    static fn kingdom() {
        return "animalia"                     // static methods have no `this`
    }
}

class Dog extends Animal {
    constructor(name) {
        super::constructor(name)              // parent constructor
    }

    public fn speak() {
        return "woof"                         // overrides Animal.speak
    }

    public fn parent_speak() {
        return super::speak()                 // parent implementation
    }
}

const rex = new Dog("Rex")

print(rex.describe())      // woof Rex (dynamic dispatch)
print(rex::describe())     // same, called with `::` from outside
print(rex.parent_speak())  // ...
print(Dog.kingdom())       // animalia (statics always use `.`)
```

Rules:

| Syntax | Meaning |
|--------|---------|
| `public fn` / `private fn` | Instance method. `public` is the default. |
| `static fn` | Static method. Called as `.Method()` inside the class or `Class.Method()` outside. |
| `public x = value` / `private x = value` | Instance field with a default value. `public` is the default. |
| `constructor(params) { }` | Runs on `new Class(args)`. |
| `this.field` | Field access inside instance methods. |
| `::Method()` | Calls an instance method with the current `this` (dynamic dispatch). |
| `.Method()` | Calls a static method of the current class. |
| `instance::Method()` | Calls an instance method from outside, binding `this` to that instance. |
| `Class.Method()` | Calls a static method from outside (statics never use `::`). |
| `super::Method()` | Calls the parent implementation. |
| `super::constructor(args)` | Calls the parent constructor (only inside a constructor). |
| `new Class(args)` | Expression that creates an instance. |

- Private members are only accessible from methods of the class that defines them; they are not inherited.
- A subclass cannot redeclare an inherited field, or change a method between static and instance.
- If a class defines no constructor, the nearest inherited constructor is used.
- Fields are initialized (parent first) before the constructor runs.

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

`if` `elseif` `else` `while` `for` `foreach` `fn` `return` `local` `const` `true` `false` `null` `and` `or` `not` `in` `break` `continue` `class` `extends` `new` `static` `public` `private` `this` `super` `constructor`

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

Python classes are supported too — scripts can instantiate them with `new` and access their attributes and methods:

```python
class Counter:
    def __init__(self, start=0):
        self.count = start

    def bump(self, n=1):
        self.count += n
        return self.count

runtime = KoskriptRuntime({"print": print, "Counter": Counter})
runtime.execute("""
const counter = new Counter(5)
print(counter.count)      // 5
print(counter.bump())     // 6
counter.count = 10
""")
```

Instances returned by registered functions work the same way. Dunder attributes (`__x__`) are blocked, and a Koskript class cannot `extends` a Python class.

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
- [x] PyPI package
- [ ] Custom parser (remove Lark dependency)
- [ ] VM-based execution

---

## License

Koskript is licensed under the Mozilla Public License 2.0 (MPL-2.0).

You are free to use, modify, and redistribute Koskript. However, you may not redistribute this project under a different name or claim authorship of the Koskript language.

**Koskript is a trademark of Alesis.**

---

*Built with ❤️ by Alesis*
