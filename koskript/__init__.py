from lark import Lark
from .lang.emtypes import KoskriptObject
from .lang.interpreter import KoskripInterpreter
from .lang.astgen import KoskriptTransformer
import pathlib, os

grammar_file = open(os.path.join(pathlib.Path(__file__).resolve().parent, "grammar.lark"), "r")
grammar = Lark(
    grammar_file, parser="lalr", maybe_placeholders=False
)

class KoskriptRuntime(object):
    def __init__(self, _globals_: dict[str, KoskriptObject] = {}):
        self.globals = _globals_

        self.__interpreter__ = KoskripInterpreter()
        self.__ast__ = KoskriptTransformer()
        for name, glob in self.globals.items():
            self.__interpreter__.set_global(name, glob)

    def execute(self, code):
        tree = grammar.parse(code)
        ast = self.__ast__.transform(tree)

        if type(ast) != list:
            ast = [ast]

        self.__interpreter__.run(ast)

__ALL__ = ["KoskriptRuntime", "KoskriptObject"]