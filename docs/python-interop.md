# Python Interop

Koskript is designed to be embedded: any Python value or callable you expose
becomes available to scripts. Values are wrapped in a `KoskriptObject`
automatically, so you can pass plain functions and objects.

## Registering values

```python
import math
import time
from koskript import KoskriptRuntime

runtime = KoskriptRuntime({
    "print": print,
    "sqrt": math.sqrt,
})

# register() is chainable
runtime.register("now", time.time)

# item assignment works too
runtime["pi"] = math.pi
```

Scripts see them as regular globals:

```koskript
print(sqrt(16))
print(now() > 0)
```

You can also register many values at once and override existing names:

```python
runtime.register_many({"sqrt": math.isqrt})   # replaces the previous sqrt
```

## Python objects

Objects are exposed as-is. Attribute access, method calls and item access work
in scripts, and mutating attributes from Python is visible both ways:

```python
class Session:
    def __init__(self):
        self.user = "guest"
        self.log = []

    def login(self, name):
        self.user = name
        self.log.append(name)
        return True


runtime = KoskriptRuntime({"session": Session()})
runtime.execute("""
print(session.user)        // guest
session.login("aleix")
session.count = 1          // new attribute
print(len(session.log))    // 1
""")
```

Instances returned by registered functions work the same way, and so do
registered Python classes.

## Python classes

Python classes can be instantiated from scripts with `new`, and their
attributes and methods behave like native ones:

```python
class Counter:
    VERSION = 2

    def __init__(self, start=0):
        self.count = start

    def bump(self, n=1):
        self.count += n
        return self.count

    @staticmethod
    def make(start=0):
        return Counter(start)


runtime = KoskriptRuntime({"Counter": Counter})
runtime.execute("""
const c = new Counter(5)
print(c.count)            // 5
print(c.bump())           // 6
print(c.bump(4))          // 10
print(Counter.VERSION)    // 2
print(Counter.make(7).count)  // 7
""")
```

Details and limits:

- `new PyClass(args)` calls the Python constructor with positional arguments.
- Attribute reads use `getattr`, attribute writes use `setattr`. Unknown
  attributes raise a Koskript `RuntimeError`.
- Static attributes and static methods are available from the class.
- Dunder attributes (`__x__`) are blocked, so scripts cannot reach Python
  internals such as `__class__` or `__dict__`.
- A Koskript class cannot `extends` a Python class.
- Exceptions raised inside Python code propagate to the host as regular Python
  exceptions; they are not wrapped in `koskript.Errors`.

## Type names

`type(value)` returns a Koskript type name for native values and the Python
type name for everything else:

```koskript
type({})          // map
type("x")         // string
```

```python
runtime = KoskriptRuntime({"session": Session(), "Session": Session})
runtime.execute('type(session)')   # "Session"
runtime.execute('type(Session)')   # "class"
```

## Iterables

`for` accepts any Python iterable, and `foreach` accepts any object with an
`items()` method, so generators, ranges and custom containers work naturally:

```python
runtime = KoskriptRuntime({"ports": range(8000, 8003)})
runtime.execute("""
for (port in ports) {
    print(port)
}
""")
```
