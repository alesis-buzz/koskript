# Getting Started

## Installation

Install from PyPI:

```bash
pip install -U koskript
```

Or clone the repository and import it directly:

```bash
git clone https://github.com/alesis-buzz/koskript.git
```

Koskript has a single runtime dependency, [Lark](https://github.com/lark-parser/lark).

## Your first script

Create a runtime and execute some code. Python values passed to the runtime are
wrapped automatically, so plain functions work out of the box:

```python
from koskript import KoskriptRuntime

runtime = KoskriptRuntime({
    "print": print
})

runtime.execute("""
local x = 10
local y = 26

print(x + y)
""")
```

Output:

```
36
```

`print` is part of the [standard library](standard-library.md) and writes to
stdout by default, so `KoskriptRuntime()` works without passing anything. Any
global you provide overrides the standard library version.

## A complete example

```koskript
// Student grade checker
local students = {
    "Aleix": { "age": 17, "grade": 95 },
    "Maria": { "age": 15, "grade": 72 },
    "Juan":  { "age": 18, "grade": 88 }
}

const passing_grade = 75

foreach (name, data in students) {
    if (data.grade >= passing_grade) {
        print("PASS:", name, "->", data.grade)
    } elseif (data.grade >= 60) {
        print("NEAR PASS:", name, "->", data.grade)
    } else {
        print("FAIL:", name, "->", data.grade)
    }
}
```

Output:

```
PASS: Aleix -> 95
NEAR PASS: Maria -> 72
PASS: Juan -> 88
```

## Where to go next

- [Language reference](language.md) — syntax and semantics.
- [Classes](classes.md) — objects, inheritance and visibility.
- [Standard library](standard-library.md) — builtins, arrays, strings, math, JSON.
- [Python interop](python-interop.md) — expose your own Python API to scripts.
- [Embedding guide](embedding.md) — runtimes, errors and configuration.
