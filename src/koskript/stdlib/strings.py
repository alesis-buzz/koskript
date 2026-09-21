from .helpers import arity, binary, expect_int, expect_type, unary
from ..lang.errors import Errors


def _expect_string(name, value):
    return expect_type(name, value, str, "a string")


def _upper(*args):
    return _expect_string("string.upper", unary("string.upper", args)).upper()


def _lower(*args):
    return _expect_string("string.lower", unary("string.lower", args)).lower()


def _trim(*args):
    return _expect_string("string.trim", unary("string.trim", args)).strip()


def _split(*args):
    text, separator = binary("string.split", args)
    _expect_string("string.split", text)
    _expect_string("string.split", separator)
    if separator == "":
        raise Errors.RuntimeError("string.split() separator cannot be empty")
    return text.split(separator)


def _starts_with(*args):
    text, prefix = binary("string.starts_with", args)
    _expect_string("string.starts_with", text)
    _expect_string("string.starts_with", prefix)
    return text.startswith(prefix)


def _ends_with(*args):
    text, suffix = binary("string.ends_with", args)
    _expect_string("string.ends_with", text)
    _expect_string("string.ends_with", suffix)
    return text.endswith(suffix)


def _replace(*args):
    arity("string.replace", args, 3, 3)
    text, old, new = args
    _expect_string("string.replace", text)
    _expect_string("string.replace", old)
    _expect_string("string.replace", new)
    return text.replace(old, new)


def _find(*args):
    text, sub = binary("string.find", args)
    _expect_string("string.find", text)
    _expect_string("string.find", sub)
    return text.find(sub)


def _contains(*args):
    text, sub = binary("string.contains", args)
    _expect_string("string.contains", text)
    _expect_string("string.contains", sub)
    return sub in text


def _slice(*args):
    arity("string.slice", args, 2, 3)
    text = _expect_string("string.slice", args[0])
    start = expect_int("string.slice", args[1])
    end = None if len(args) == 2 else expect_int("string.slice", args[2])
    return text[start:end]


def _repeat(*args):
    text, count = binary("string.repeat", args)
    _expect_string("string.repeat", text)
    count = expect_int("string.repeat", count)
    if count < 0:
        raise Errors.RuntimeError("string.repeat() count cannot be negative")
    return text * count


def _pad_left(*args):
    arity("string.pad_left", args, 2, 3)
    text = _expect_string("string.pad_left", args[0])
    width = expect_int("string.pad_left", args[1])
    fill = " " if len(args) == 2 else _expect_string("string.pad_left", args[2])
    if len(fill) != 1:
        raise Errors.MismatchType(
            "string.pad_left() expected a single character as fill")
    return text.rjust(width, fill)


def _pad_right(*args):
    arity("string.pad_right", args, 2, 3)
    text = _expect_string("string.pad_right", args[0])
    width = expect_int("string.pad_right", args[1])
    fill = " " if len(args) == 2 else _expect_string("string.pad_right", args[2])
    if len(fill) != 1:
        raise Errors.MismatchType(
            "string.pad_right() expected a single character as fill")
    return text.ljust(width, fill)


def _chars(*args):
    return list(_expect_string("string.chars", unary("string.chars", args)))


def build():
    return {
        "string": {
            "upper": _upper,
            "lower": _lower,
            "trim": _trim,
            "split": _split,
            "starts_with": _starts_with,
            "ends_with": _ends_with,
            "replace": _replace,
            "find": _find,
            "contains": _contains,
            "slice": _slice,
            "repeat": _repeat,
            "pad_left": _pad_left,
            "pad_right": _pad_right,
            "chars": _chars,
        }
    }
