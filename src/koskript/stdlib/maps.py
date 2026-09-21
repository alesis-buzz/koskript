from .helpers import binary, expect_type, unary
from ..lang.errors import Errors


def _keys(*args):
    mapping = expect_type("map.keys", unary("map.keys", args), dict, "a map")
    return list(mapping.keys())


def _values(*args):
    mapping = expect_type("map.values", unary("map.values", args), dict, "a map")
    return list(mapping.values())


def _has(*args):
    mapping, key = binary("map.has", args)
    expect_type("map.has", mapping, dict, "a map")
    return key in mapping


def _remove(*args):
    mapping, key = binary("map.remove", args)
    expect_type("map.remove", mapping, dict, "a map")
    if key not in mapping:
        raise Errors.RuntimeError(f"map.remove() key {key!r} is not in the map")
    return mapping.pop(key)


def _merge(*args):
    target, other = binary("map.merge", args)
    expect_type("map.merge", target, dict, "a map")
    expect_type("map.merge", other, dict, "a map")
    target.update(other)
    return target


def build():
    return {
        "map": {
            "keys": _keys,
            "values": _values,
            "has": _has,
            "remove": _remove,
            "merge": _merge,
        }
    }
