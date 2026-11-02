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

    public fun speak() {
        return "..."
    }

    public fun describe() {
        return ::speak() + " " + this.name   // :: calls an instance method
    }

    private fun drain() {
        this.energy = this.energy - 10
    }

    static fun kingdom() {
        return "animalia"                     // static methods have no `this`
    }
}

class Dog extends Animal {
    constructor(name) {
        super::constructor(name)              // parent constructor
    }

    public fun speak() {
        return "woof"                         // overrides Animal.speak
    }

    public fun parent_speak() {
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
| `public fun` / `private fun` | Instance method. `public` is the default. |
| `static fun` | Static method. Called as `.Method()` inside the class or `Class.Method()` outside. |
| `public x = value` / `private x = value` | Instance field with a default value. `public` is the default. |
| `constructor(params) { }` | Runs on `new Class(args)`. |
| `this.field` | Field access inside instance methods. |
| `::Method()` | Calls an instance method with the current `this` (dynamic dispatch). |
| `.Method()` | Calls a static method of the current class. |
| `instance::Method()` | Calls an instance method from outside, binding `this` to that instance. |
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

rex::speak()       // `::`: instance method, binds `this` to rex
::speak()          // `::`: instance method on the current `this` (inside a class)
super::speak()     // `::`: the parent implementation, never the override
Dog.kingdom()      // `.`: statics always use `.`, never `::`
.kingdom()         // `.`: static of the current class, inside the class
```

Instance methods are **only** called with `::`. `.` is reserved for
fields, keys, statics and plain callable values.

**Rule of thumb:** use `.` for fields, keys, statics and plain callable
values; use `::` for instance methods (`::Method()` inside a class,
`super::` for the parent, `instance::Method()` from outside).

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

    public fun make_incrementer() {
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
