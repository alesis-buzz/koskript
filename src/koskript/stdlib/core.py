from .helpers import arity, type_name, unary
from ..lang.emtypes import ErrorInstance
from ..lang.errors import Errors


def to_string(value, seen=None):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    if isinstance(value, ErrorInstance):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, (list, dict)):
        seen = set() if seen is None else seen
        if id(value) in seen:
            return "<cycle>"
        seen.add(id(value))
        try:
            if isinstance(value, list):
                return "[" + ", ".join(to_string(item, seen) for item in value) + "]"
            parts = []
            for key, item in value.items():
                shown = f'"{key}"' if isinstance(key, str) else to_string(key, seen)
                parts.append(f"{shown}: {to_string(item, seen)}")
            return "{" + ", ".join(parts) + "}"
        finally:
            seen.discard(id(value))
    return repr(value)


def _deep_copy(value, seen=None):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if not isinstance(value, (list, dict)):
        raise Errors.MismatchType(
            f"copy() only supports arrays, maps and primitive values, got {type_name(value)}")
    seen = {} if seen is None else seen
    if id(value) in seen:
        return seen[id(value)]
    if isinstance(value, list):
        result = []
        seen[id(value)] = result
        result.extend(_deep_copy(item, seen) for item in value)
        return result
    result = {}
    seen[id(value)] = result
    for key, item in value.items():
        result[key] = _deep_copy(item, seen)
    return result


def _type(*args):
    return type_name(unary("type", args))


def _len(*args):
    value = unary("len", args)
    try:
        return len(value)
    except TypeError:
        raise Errors.MismatchType(
            f"len() expected an array, map or string, got {type_name(value)}")


def _str(*args):
    return to_string(unary("str", args))


def _int(*args):
    value = unary("int", args)
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            raise Errors.RuntimeError(f'int() cannot parse "{value}" as an int')
    raise Errors.MismatchType(
        f"int() expected a number or string, got {type_name(value)}")


def _float(*args):
    value = unary("float", args)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            raise Errors.RuntimeError(f'float() cannot parse "{value}" as a float')
    raise Errors.MismatchType(
        f"float() expected a number or string, got {type_name(value)}")


def _bool(*args):
    value = unary("bool", args)
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value != ""
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def _range(*args):
    arity("range", args, 1, 3)
    for value in args:
        if isinstance(value, bool) or not isinstance(value, int):
            raise Errors.MismatchType(
                f"range() expected int arguments, got {type_name(value)}")
    return range(*args)


def _copy(*args):
    return _deep_copy(unary("copy", args))


def build():
    return {
        "print": print,
        "len": _len,
        "type": _type,
        "str": _str,
        "int": _int,
        "float": _float,
        "bool": _bool,
        "range": _range,
        "copy": _copy,
    }
