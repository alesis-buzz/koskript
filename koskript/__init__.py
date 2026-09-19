from lark import Lark
from .lang.emtypes import KoskriptObject
from .lang.interpreter import KoskripInterpreter
from .lang.astgen import KoskriptTransformer
from .lang.errors import Errors
import pathlib, os

_grammar_path = os.path.join(pathlib.Path(__file__).resolve().parent, "grammar.lark")
with open(_grammar_path, "r") as _grammar_file:
    grammar = Lark(_grammar_file, parser="lalr", maybe_placeholders=False)


def _wrap(value):
    return value if isinstance(value, KoskriptObject) else KoskriptObject(value=value)


class KoskriptRuntime(object):
    """Embeddable Koskript runtime.

    Any Python value or callable exposed to scripts is wrapped automatically,
    so you can pass plain functions without building ``KoskriptObject`` by hand.

    >>> rt = KoskriptRuntime({"print": print})
    >>> rt.execute("local x = 10\\nx + 26")
    36
    """

    def __init__(self, globals=None, _globals_=None):
        if _globals_ is not None:
            globals = {**(globals or {}), **_globals_}

        self.globals = {}
        self.__interpreter__ = KoskripInterpreter()
        self.__ast__ = KoskriptTransformer()

        if globals:
            self.register_many(globals)

    def register(self, name: str, value):
        """Expose a Python value or callable to scripts.

        Returns the runtime so calls can be chained.
        """
        obj = _wrap(value)
        self.globals[name] = obj
        self.__interpreter__.set_global(name, obj)
        return self

    def register_many(self, mapping: dict):
        for name, value in mapping.items():
            self.register(name, value)
        return self

    def __setitem__(self, name: str, value):
        self.register(name, value)

    def __getitem__(self, name: str):
        return self.__interpreter__.get_global(name).value

    def execute(self, code: str):
        """Parse and run ``code``.

        Returns the value of the last evaluated expression, or the value of a
        top-level ``return`` if the script uses one.
        """
        tree = grammar.parse(code)
        ast = self.__ast__.transform(tree)

        if not isinstance(ast, list):
            ast = [ast]

        return self.__interpreter__.run(ast)


def run(code: str, globals: dict = None, **kwargs):
    """One-shot convenience helper.

    >>> run("print(1 + 2)", print=print)
    3
    """
    merged = dict(globals or {})
    merged.update(kwargs)
    return KoskriptRuntime(merged).execute(code)


__all__ = ["KoskriptRuntime", "KoskriptObject", "Errors", "run"]
