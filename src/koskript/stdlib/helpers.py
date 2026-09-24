import inspect

from ..lang.emtypes import (
    BoundMethod, Function, KoskriptClass, KoskriptInstance, Module)
from ..lang.errors import Errors


def type_name(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "map"
    if isinstance(value, KoskriptClass) or inspect.isclass(value):
        return "class"
    if isinstance(value, KoskriptInstance):
        return "instance"
    if isinstance(value, Module):
        return "module"
    if isinstance(value, (Function, BoundMethod)):
        return "function"
    return type(value).__name__


def arity(name: str, args: tuple, minimum: int, maximum: int = None):
    count = len(args)
    if count >= minimum and (maximum is None or count <= maximum):
        return
    if maximum is None:
        expected = f"at least {minimum}"
    elif minimum == maximum:
        expected = f"{minimum}"
    else:
        expected = f"between {minimum} and {maximum}"
    raise Errors.MismatchType(
        f"{name}() expected {expected} argument(s), got {count}")


def unary(name: str, args: tuple):
    arity(name, args, 1, 1)
    return args[0]


def binary(name: str, args: tuple):
    arity(name, args, 2, 2)
    return args[0], args[1]


def expect_type(name: str, value, expected_type, description: str):
    if not isinstance(value, expected_type):
        raise Errors.MismatchType(
            f"{name}() expected {description}, got {type_name(value)}")
    return value


def expect_int(name: str, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise Errors.MismatchType(
            f"{name}() expected an int, got {type_name(value)}")
    return value


def expect_number(name: str, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Errors.MismatchType(
            f"{name}() expected a number, got {type_name(value)}")
    return value
