# Standard Library

Koskript ships a standard library implemented in Python. It is registered
automatically and can be disabled or overridden.

## Activation

```python
from koskript import KoskriptRuntime, run

runtime = KoskriptRuntime()                       # stdlib enabled (default)
runtime = KoskriptRuntime({"print": my_print})    # override any name
runtime = KoskriptRuntime(stdlib=False)           # no standard library
run("print(1 + 2)")                               # run() enables it too
```

The standard library is registered **before** the globals you pass in, so your
values always win. `runtime.register("print", sink)` overrides a name later as
well.

Namespaces (`map`, `array`, `string`, `math`, `json`) are plain maps created
fresh for every runtime, so one runtime cannot corrupt another. A script can
`math.pi = 3` and only that runtime is affected. You can replace a whole
namespace by registering a map with the same name.

For custom setups, `build_globals()` returns a fresh dictionary with the whole
standard library:

```python
from koskript import build_globals

runtime = KoskriptRuntime(stdlib=False)
runtime.register_many(build_globals())
```

`KoskriptRuntime` also plugs a bridge into the higher-order array functions
(`map`, `filter`, `reduce`, `sort_by`, `each`). When you install
`build_globals()` by hand those five raise a clear `RuntimeError` if called.

## Conventions

- Functions validate their arguments and raise `Errors.MismatchType` for wrong
  types or arity, and `Errors.RuntimeError` for domain errors (out-of-range
  indexes, invalid JSON, `sqrt(-1)`...).
- Mutating functions return the collection they modified, so calls can be
  chained: `array.push(items, 1)` mutates `items` and returns it.
- Functions that remove an element return the removed element.
- Queries return plain values (`bool`, `int`, new arrays...).

## Core builtins

| Function | Description |
|---|---|
| `print(values...)` | Writes to stdout (space separated, newline at the end). Override it to capture output. |
| `len(value)` | Length of an array, map, string or any sized value. |
| `type(value)` | Type name as a string (see [Types](language.md#types)). |
| `str(value)` | Human-readable string. Maps and arrays are formatted recursively; cycles render as `<cycle>`. |
| `int(value)` | Converts `bool`, `int`, `float` (truncates) or a numeric string. |
| `float(value)` | Converts `bool`, `int`, `float` or a numeric string. |
| `bool(value)` | Truthiness of any value. |
| `range([start,] stop[, step])` | Iterable sequence of ints. Use it with `for`; it is also indexable. |
| `copy(value)` | Deep copy of arrays, maps and primitives. |

```koskript
print(len([1, 2, 3]))          // 3
print(type(3.5))                // float
print(str({ "a": [1, 2] }))     // {"a": [1, 2]}
print(int("42") + 1)            // 43

local total = 0
for (i in range(1, 4)) { total = total + i }
print(total)                    // 6

local original = { "x": [1] }
local clone = copy(original)
array.push(clone.x, 2)
print(len(original.x), len(clone.x))   // 1 2
```

## `map`

| Function | Description |
|---|---|
| `map.keys(m)` | New array with the keys. |
| `map.values(m)` | New array with the values. |
| `map.has(m, key)` | `true` if the key exists. |
| `map.remove(m, key)` | Removes and returns the value. Errors if the key is missing. |
| `map.merge(target, other)` | Copies the entries of `other` into `target` and returns `target`. |

```koskript
local config = { "debug": true, "port": 8080 }

print(str(map.keys(config)))     // [debug, port]
print(map.has(config, "port"))   // true
print(map.remove(config, "port"))// 8080

map.merge(config, { "host": "localhost" })
print(len(config))               // 2
```

## `array`

| Function | Description |
|---|---|
| `array.push(a, value)` | Appends and returns `a`. |
| `array.pop(a)` | Removes and returns the last element. Errors if empty. |
| `array.insert(a, index, value)` | Inserts at `index` (negative or `len` allowed) and returns `a`. |
| `array.remove_at(a, index)` | Removes and returns the element at `index`. |
| `array.clear(a)` | Removes every element and returns `a`. |
| `array.sort(a)` | Sorts in place and returns `a`. Errors if elements are not comparable. |
| `array.sort_by(a, fn)` | Stable sort by the key returned by `fn`. |
| `array.reverse(a)` | Reverses in place and returns `a`. |
| `array.slice(a, start[, end])` | New array with the range (negative indexes allowed). |
| `array.join(a, separator)` | Joins an array of strings into a single string. |
| `array.index_of(a, value)` | Index of the first match, or `-1`. |
| `array.contains(a, value)` | `true` if the value is present. |
| `array.map(a, fn)` | New array with `fn(item)` for every item. |
| `array.filter(a, fn)` | New array with the items where `fn(item)` is truthy. |
| `array.reduce(a, fn[, initial])` | Folds the array with `fn(accumulator, item)`. |
| `array.each(a, fn)` | Calls `fn(item)` for every item and returns `null`. |

Higher-order callbacks can be lambdas, functions, bound methods or Python
callables:

```koskript
local numbers = [3, 1, 2]

print(array.map(numbers, (x) { return x * 2 }))     // [6, 2, 4]
print(array.filter(numbers, (x) { return x > 1 }))  // [3, 2]
print(array.reduce(numbers, (acc, x) { return acc + x }, 0))  // 6

array.sort(numbers)
print(array.join(array.map(numbers, str), ", "))    // 1, 2, 3

array.each(numbers, (x) { print("value:", x) })
```

`array.sort_by` uses the key returned by the callback and keeps the original
order of equal keys:

```koskript
local words = ["bb", "a", "ccc"]
array.sort_by(words, (w) { return len(w) })
print(array.join(words, " "))   // a bb ccc
```

## `string`

| Function | Description |
|---|---|
| `string.upper(s)` / `string.lower(s)` | Change case. |
| `string.trim(s)` | Removes leading and trailing whitespace. |
| `string.split(s, separator)` | Splits into an array; separator cannot be empty. |
| `string.starts_with(s, prefix)` / `string.ends_with(s, suffix)` | Prefix/suffix checks. |
| `string.replace(s, old, new)` | Replaces every occurrence. |
| `string.find(s, sub)` | Index of the first occurrence, or `-1`. |
| `string.contains(s, sub)` | `true` if `sub` appears in `s`. |
| `string.slice(s, start[, end])` | Substring (negative indexes allowed). |
| `string.repeat(s, count)` | Repeats `s` `count` times. |
| `string.pad_left(s, width[, fill])` / `string.pad_right(...)` | Pads to `width` using a single-character `fill` (space by default). |
| `string.chars(s)` | Array of single-character strings. |

```koskript
print(string.upper("hello"))                  // HELLO
print(str(string.split("a,b,c", ",")))        // [a, b, c]
print(string.replace("a-b-c", "-", "+"))      // a+b+c
print(string.pad_left("7", 3, "0"))           // 007
print(string.contains("hello", "ell"))        // true
```

## `math`

| Name | Description |
|---|---|
| `math.pi`, `math.e` | Constants. |
| `math.abs(x)` | Absolute value. |
| `math.floor(x)` / `math.ceil(x)` | Round down/up to an `int`. |
| `math.round(x[, digits])` | Python rounding (banker's rounding); with `digits` returns a `float`. |
| `math.sqrt(x)` | Square root. Errors for negative values. |
| `math.pow(base, exponent)` | Power. Integer result when both are ints and the exponent is non-negative. |
| `math.min(...)` / `math.max(...)` | Smallest/largest of two or more numbers, or of a single array. |
| `math.clamp(x, low, high)` | Restricts `x` to the `[low, high]` range. |
| `math.random()` | Float in `[0, 1)`. |
| `math.random_int(low, high)` | Inclusive random integer. |
| `math.log(x)` / `math.exp(x)` | Natural logarithm and exponential. |
| `math.sin(x)` / `math.cos(x)` / `math.tan(x)` | Trigonometry (radians). |

```koskript
print(math.sqrt(16))              // 4.0
print(math.pow(2, 3))             // 8
print(math.max([3, 1, 2]))        // 3
print(math.clamp(5, 0, 3))        // 3
print(math.round(math.pi, 2))     // 3.14
```

Domain errors such as `math.sqrt(-1)` or `math.log(0)` raise
`Errors.RuntimeError`.

## `json`

| Function | Description |
|---|---|
| `json.encode(value)` | Serializes arrays, maps and primitives to a JSON string (UTF-8, non-ASCII characters are kept). |
| `json.decode(text)` | Parses a JSON string into arrays, maps and primitives. |

```koskript
local text = json.encode({ "name": "Koskript", "tags": ["dsl", "python"] })
print(text)                       // {"name": "Koskript", "tags": ["dsl", "python"]}

local data = json.decode(text)
print(data.name)                  // Koskript
print(data.tags[1])               // python
```

Functions, class instances and other runtime objects cannot be encoded and
raise `Errors.RuntimeError`. Invalid JSON raises `Errors.RuntimeError` with the
parser message; non-string input raises `Errors.MismatchType`.

## Errors

```koskript
len()          // MismatchType: len() expected 1 argument(s), got 0
int("abc")     // RuntimeError: int() cannot parse "abc" as an int
array.pop([])  // RuntimeError: array.pop() cannot pop from an empty array
```

Errors are available from Python as `koskript.Errors`; see the
[embedding guide](embedding.md#error-handling).
