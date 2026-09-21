import json

from .helpers import type_name, unary
from ..lang.errors import Errors


def _encode(*args):
    value = unary("json.encode", args)
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise Errors.RuntimeError(f"json.encode() cannot encode that value: {exc}")


def _decode(*args):
    text = unary("json.decode", args)
    if not isinstance(text, str):
        raise Errors.MismatchType(
            f"json.decode() expected a string, got {type_name(text)}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise Errors.RuntimeError(f"json.decode() found invalid JSON: {exc}")


def build():
    return {
        "json": {
            "encode": _encode,
            "decode": _decode,
        }
    }
