import functools

from .helpers import arity, binary, expect_int, expect_type, type_name, unary
from ..lang.emtypes import BoundMethod, Function
from ..lang.errors import Errors


def _expect_array(name, value):
    return expect_type(name, value, list, "an array")


def _expect_callable(name, value):
    if isinstance(value, (Function, BoundMethod)) or callable(value):
        return value
    raise Errors.MismatchType(
        f"{name}() expected a function, got {type_name(value)}")


def _bridge_missing(*args):
    raise Errors.RuntimeError(
        "this array function needs a Koskript runtime to call back into the script")


def _push(*args):
    array, value = binary("array.push", args)
    _expect_array("array.push", array)
    array.append(value)
    return array


def _pop(*args):
    array = _expect_array("array.pop", unary("array.pop", args))
    if not array:
        raise Errors.RuntimeError("array.pop() cannot pop from an empty array")
    return array.pop()


def _insert(*args):
    arity("array.insert", args, 3, 3)
    array, index, value = args
    _expect_array("array.insert", array)
    expect_int("array.insert", index)
    if not -len(array) <= index <= len(array):
        raise Errors.RuntimeError(
            f"array.insert() index {index} is out of range")
    array.insert(index, value)
    return array


def _remove_at(*args):
    array, index = binary("array.remove_at", args)
    _expect_array("array.remove_at", array)
    expect_int("array.remove_at", index)
    try:
        return array.pop(index)
    except IndexError:
        raise Errors.RuntimeError(
            f"array.remove_at() index {index} is out of range")


def _clear(*args):
    array = _expect_array("array.clear", unary("array.clear", args))
    array.clear()
    return array


def _sort(*args):
    array = _expect_array("array.sort", unary("array.sort", args))
    try:
        array.sort()
    except TypeError:
        raise Errors.RuntimeError(
            "array.sort() cannot compare the elements of the array")
    return array


def _sort_by(call, *args):
    array, key = binary("array.sort_by", args)
    _expect_array("array.sort_by", array)
    _expect_callable("array.sort_by", key)
    decorated = [(call(key, [item]), item) for item in array]
    try:
        decorated.sort(key=lambda pair: pair[0])
    except TypeError:
        raise Errors.RuntimeError(
            "array.sort_by() produced keys that cannot be compared")
    array[:] = [item for _, item in decorated]
    return array


def _reverse(*args):
    array = _expect_array("array.reverse", unary("array.reverse", args))
    array.reverse()
    return array


def _slice(*args):
    arity("array.slice", args, 2, 3)
    array = _expect_array("array.slice", args[0])
    start = expect_int("array.slice", args[1])
    end = None if len(args) == 2 else expect_int("array.slice", args[2])
    return array[start:end]


def _join(*args):
    array, separator = binary("array.join", args)
    _expect_array("array.join", array)
    expect_type("array.join", separator, str, "a string")
    for item in array:
        expect_type("array.join", item, str, "an array of strings")
    return separator.join(array)


def _index_of(*args):
    array, value = binary("array.index_of", args)
    _expect_array("array.index_of", array)
    try:
        return array.index(value)
    except ValueError:
        return -1


def _contains(*args):
    array, value = binary("array.contains", args)
    _expect_array("array.contains", array)
    return value in array


def _map(call, *args):
    array, fn = binary("array.map", args)
    _expect_array("array.map", array)
    _expect_callable("array.map", fn)
    return [call(fn, [item]) for item in array]


def _filter(call, *args):
    array, fn = binary("array.filter", args)
    _expect_array("array.filter", array)
    _expect_callable("array.filter", fn)
    return [item for item in array if call(fn, [item])]


def _reduce(call, *args):
    arity("array.reduce", args, 2, 3)
    array = _expect_array("array.reduce", args[0])
    fn = _expect_callable("array.reduce", args[1])
    if len(args) == 3:
        accumulator, start = args[2], 0
    else:
        if not array:
            raise Errors.RuntimeError(
                "array.reduce() cannot reduce an empty array without an initial value")
        accumulator, start = array[0], 1
    for item in array[start:]:
        accumulator = call(fn, [accumulator, item])
    return accumulator


def _each(call, *args):
    array, fn = binary("array.each", args)
    _expect_array("array.each", array)
    _expect_callable("array.each", fn)
    for item in array:
        call(fn, [item])
    return None


def build(call_value=None):
    call = call_value if call_value is not None else _bridge_missing

    return {
        "array": {
            "push": _push,
            "pop": _pop,
            "insert": _insert,
            "remove_at": _remove_at,
            "clear": _clear,
            "sort": _sort,
            "sort_by": functools.partial(_sort_by, call),
            "reverse": _reverse,
            "slice": _slice,
            "join": _join,
            "index_of": _index_of,
            "contains": _contains,
            "map": functools.partial(_map, call),
            "filter": functools.partial(_filter, call),
            "reduce": functools.partial(_reduce, call),
            "each": functools.partial(_each, call),
        }
    }
