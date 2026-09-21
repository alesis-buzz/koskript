import math
import random as _pyrandom

from .helpers import arity, binary, expect_int, expect_number, unary
from ..lang.errors import Errors


def _guard(name, fn, *values):
    try:
        return fn(*values)
    except ValueError:
        raise Errors.RuntimeError(f"{name}() is not defined for that value")
    except OverflowError:
        raise Errors.RuntimeError(f"{name}() overflowed")


def _abs(*args):
    return abs(expect_number("math.abs", unary("math.abs", args)))


def _floor(*args):
    value = expect_number("math.floor", unary("math.floor", args))
    return _guard("math.floor", math.floor, value)


def _ceil(*args):
    value = expect_number("math.ceil", unary("math.ceil", args))
    return _guard("math.ceil", math.ceil, value)


def _round(*args):
    arity("math.round", args, 1, 2)
    value = expect_number("math.round", args[0])
    if len(args) == 1:
        return _guard("math.round", round, value)
    digits = expect_int("math.round", args[1])
    return _guard("math.round", round, value, digits)


def _sqrt(*args):
    value = expect_number("math.sqrt", unary("math.sqrt", args))
    return _guard("math.sqrt", math.sqrt, value)


def _pow(*args):
    base, exponent = binary("math.pow", args)
    expect_number("math.pow", base)
    expect_number("math.pow", exponent)
    if isinstance(base, int) and isinstance(exponent, int) and exponent >= 0:
        return base ** exponent
    return _guard("math.pow", math.pow, base, exponent)


def _extreme(name, pick, args):
    values = list(args)
    if len(values) == 1 and isinstance(values[0], list):
        values = values[0]
    elif len(values) < 2:
        raise Errors.MismatchType(
            f"{name}() expected at least two numbers or a single array")
    if not values:
        raise Errors.RuntimeError(f"{name}() cannot be used on an empty array")
    for value in values:
        expect_number(name, value)
    return pick(values)


def _min(*args):
    return _extreme("math.min", min, args)


def _max(*args):
    return _extreme("math.max", max, args)


def _clamp(*args):
    arity("math.clamp", args, 3, 3)
    value, low, high = (expect_number("math.clamp", arg) for arg in args)
    if low > high:
        raise Errors.RuntimeError(
            "math.clamp() lower bound is greater than the upper bound")
    return min(max(value, low), high)


def _random(*args):
    arity("math.random", args, 0, 0)
    return _pyrandom.random()


def _random_int(*args):
    low, high = binary("math.random_int", args)
    expect_int("math.random_int", low)
    expect_int("math.random_int", high)
    if low > high:
        raise Errors.RuntimeError(
            "math.random_int() lower bound is greater than the upper bound")
    return _pyrandom.randint(low, high)


def _log(*args):
    value = expect_number("math.log", unary("math.log", args))
    return _guard("math.log", math.log, value)


def _exp(*args):
    value = expect_number("math.exp", unary("math.exp", args))
    return _guard("math.exp", math.exp, value)


def _sin(*args):
    value = expect_number("math.sin", unary("math.sin", args))
    return _guard("math.sin", math.sin, value)


def _cos(*args):
    value = expect_number("math.cos", unary("math.cos", args))
    return _guard("math.cos", math.cos, value)


def _tan(*args):
    value = expect_number("math.tan", unary("math.tan", args))
    return _guard("math.tan", math.tan, value)


def build():
    return {
        "math": {
            "pi": math.pi,
            "e": math.e,
            "abs": _abs,
            "floor": _floor,
            "ceil": _ceil,
            "round": _round,
            "sqrt": _sqrt,
            "pow": _pow,
            "min": _min,
            "max": _max,
            "clamp": _clamp,
            "random": _random,
            "random_int": _random_int,
            "log": _log,
            "exp": _exp,
            "sin": _sin,
            "cos": _cos,
            "tan": _tan,
        }
    }
