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
| `Class.Method()` | Calls a static method from outside (statics never use `::`). |
| `super::Method()` | Calls the parent implementation. |
| `super::constructor(args)` | Calls the parent constructor (only inside a constructor). |
| `new Class(args)` | Expression that creates an instance. |

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
