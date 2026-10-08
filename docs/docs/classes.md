# Classes

Classes support single inheritance, visibility modifiers, static methods and
constructors.

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

## Syntax

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
| `instance.Method()` | Also calls an instance method from outside; works through the member value. |
| `Class.Method()` | Calls a static method from outside (statics never use `::`). |
| `super::Method()` | Calls the parent implementation. |
| `super::constructor(args)` | Calls the parent constructor (only inside a constructor). |
| `new Class(args)` | Expression that creates an instance. The class can be qualified: `new Namespace.Class(args)`. |

## Dot vs double colon

`.` is the general member operator: it reads fields and map keys, calls
static methods and calls methods through their member value. `::` is only for
instance methods — `this` is always involved.

```koskript
const rex = new Dog("Rex")

rex.speak()        // `.`: reads the member and calls it
rex::speak()       // `::`: looks the method up on the class, binds `this` to rex
::speak()          // `::`: instance method on the current `this` (inside a class)
super::speak()     // `::`: the parent implementation, never the override
Dog.kingdom()      // `.`: statics always use `.`, never `::`
.kingdom()         // `.`: static of the current class, inside the class
```

For a **public** method, `instance.Method()` and `instance::Method()` do the
same thing: both dispatch dynamically on the instance's real class. The
difference only shows in the edge cases:

| Case | `instance.Method()` | `instance::Method()` |
|------|---------------------|----------------------|
| Public method | works (dynamic dispatch) | works (dynamic dispatch) |
| Private method | only from the class that defines it | only from the class that defines it |
| Static method | error: `call it as 'Dog.kingdom()'` | same error |
| Method not defined | falls back to a field of the same name, else `'x' is not defined on 'Dog'` | `method 'x' is not defined on 'Dog'` |
| Field holding a function | calls it as a plain function | error: not a method |

Both forms also work on Python objects. `::m()` requires the attribute to
exist and actually be a method, otherwise you get `'m' is not a method of Obj`
(or `'m' is not defined on Obj`). `.` calls whatever the attribute evaluates
to, so a plain field fails later with `int is not callable`.

**Rule of thumb:** use `.` for everything (fields, keys, statics, plain
method calls) and `::` when you specifically mean an instance method:
`::Method()` inside a class, `super::` for the parent, and
`instance::Method()` from outside when you want to be explicit — or to be
sure you are calling a method and not a callable field.

## Rules

- Private members are only accessible from methods of the class that defines
  them; they are **not** inherited.
- A subclass cannot redeclare an inherited field, or change a method between
  static and instance.
- A class can only define one constructor.
- If a class defines no constructor, the nearest inherited constructor is used.
- Field initializers run parent-first, before the constructor.
- Fields cannot be `static`; only methods can.
- A Koskript class cannot `extends` a Python class. Python classes can still be
  instantiated with `new` and used from scripts — see
  [Python interop](python-interop.md).
- Method visibility is resolved at definition time: private calls are
  non-virtual, public calls use dynamic dispatch on the instance's class.

## Closures and `this`

A lambda or nested function defined inside a method captures `this`, so it can
read fields, call private methods and use `::Method()`:

```koskript
class Counter {
    private count = 0

    public fn make_incrementer() {
        return () {
            this.count = this.count + 1
            return this.count
        }
    }
}

const inc = new Counter().make_incrementer()
print(inc())   // 1
print(inc())   // 2
```
