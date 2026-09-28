from .helpers import arity, binary, expect_int, expect_type, type_name, unary
from ..lang.errors import Errors


def _expect_bytes(name, value):
    if isinstance(value, bytearray):
        return bytes(value)
    if not isinstance(value, bytes):
        raise Errors.MismatchType(
            f"{name}() expected bytes, got {type_name(value)}")
    return value


def _expect_string(name, value):
    return expect_type(name, value, str, "a string")


def _encoding(name, args):
    return "utf-8" if len(args) == 1 else _expect_string(name, args[1])


def _from_string(*args):
    arity("bytes.from_string", args, 1, 2)
    text = _expect_string("bytes.from_string", args[0])
    encoding = _encoding("bytes.from_string", args)
    try:
        return text.encode(encoding)
    except LookupError:
        raise Errors.RuntimeError(
            f"bytes.from_string() unknown encoding '{encoding}'")
    except UnicodeEncodeError as exc:
        raise Errors.RuntimeError(
            f"bytes.from_string() cannot encode the string: {exc}")


def _to_string(*args):
    arity("bytes.to_string", args, 1, 2)
    data = _expect_bytes("bytes.to_string", args[0])
    encoding = _encoding("bytes.to_string", args)
    try:
        return data.decode(encoding)
    except LookupError:
        raise Errors.RuntimeError(
            f"bytes.to_string() unknown encoding '{encoding}'")
    except UnicodeDecodeError as exc:
        raise Errors.RuntimeError(
            f"bytes.to_string() cannot decode the bytes: {exc}")


def _hex(*args):
    data = _expect_bytes("bytes.hex", unary("bytes.hex", args))
    return "0x" + data.hex()


def _from_hex(*args):
    text = _expect_string("bytes.from_hex", unary("bytes.from_hex", args)).strip()
    if text[:2] in ("0x", "0X"):
        text = text[2:]
    if len(text) % 2:
        raise Errors.RuntimeError(
            "bytes.from_hex() expected an even number of hexadecimal digits")
    try:
        return bytes.fromhex(text)
    except ValueError:
        raise Errors.RuntimeError(
            "bytes.from_hex() expected a hexadecimal string")


def _from_array(*args):
    name = "bytes.from_array"
    values = expect_type(name, unary(name, args), list, "an array")
    out = bytearray()
    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, int):
            raise Errors.MismatchType(
                f"{name}() expected ints, got {type_name(value)} at index {index}")
        if not 0 <= value <= 255:
            raise Errors.RuntimeError(
                f"{name}() value {value} at index {index} is out of range (0-255)")
        out.append(value)
    return bytes(out)


def _to_array(*args):
    return list(_expect_bytes("bytes.to_array", unary("bytes.to_array", args)))


def _contains(*args):
    data, part = binary("bytes.contains", args)
    _expect_bytes("bytes.contains", data)
    _expect_bytes("bytes.contains", part)
    return part in data


def _slice(*args):
    arity("bytes.slice", args, 2, 3)
    data = _expect_bytes("bytes.slice", args[0])
    start = expect_int("bytes.slice", args[1])
    end = None if len(args) == 2 else expect_int("bytes.slice", args[2])
    return data[start:end]


def build():
    return {
        "bytes": {
            "from_string": _from_string,
            "to_string": _to_string,
            "hex": _hex,
            "from_hex": _from_hex,
            "from_array": _from_array,
            "to_array": _to_array,
            "contains": _contains,
            "slice": _slice,
        }
    }
