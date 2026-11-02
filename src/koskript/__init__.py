import pathlib

from .lang.emtypes import (KoskriptObject, Module, Namespace, Scope, ScopeInfo,
                           ThrownSignal)
from .lang.interpreter import KoskriptInterpreter
from .lang.parser import parse
from .lang.errors import Errors
from .stdlib import build_globals
import os


def _wrap(value):
    return value if isinstance(value, KoskriptObject) else KoskriptObject(value=value)


# How many compiled sources a runtime keeps. Running the same script again is
# then free of parsing and compiling; the oldest entry is dropped past this.
_CHUNK_CACHE = 32

class KoskriptRuntime(object):
    """Embeddable Koskript runtime.

    The standard library is registered by default. Host globals are registered
    after it, so any of them can override a standard library name. Pass
    ``stdlib=False`` to skip the standard library entirely.

    Any Python value or callable exposed to scripts is wrapped automatically,
    so you can pass plain functions without building ``KoskriptObject`` by hand.

    Scripts are parsed with the native pure Python scanner and parser,
    which needs no external dependency.

    >>> rt = KoskriptRuntime({"print": print})
    >>> rt.execute("let x = 10\\nx + 26")
    36
    """

    def __init__(self, globals_map=None, _globals_=None, stdlib=True,
                 native_parser_experiment=False):
        if _globals_ is not None:
            globals_map = {**(globals_map or {}), **_globals_}

        self.globals = {}
        self.native_parser_experiment = bool(native_parser_experiment)
        self.__interpreter__ = KoskriptInterpreter()
        self.__interpreter__.module_loader = self._load_module
        self._modules = {}
        self._loading = []
        self._import_paths = []
        self._chunks = {}

        if stdlib:
            self.register_many(build_globals(self.__interpreter__.call_value))

        if globals_map:
            self.register_many(globals_map)

        # expose `loadcode` to scripts: compiles a source string into a
        # callable that runs it in this runtime
        self.register("loadcode", self._loadcode_host)

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

    def add_import_path(self, path: str):
        """Add a directory that ``import`` searches after the base directory.

        The base directory is the one of the file that contains the ``import``
        (or the current working directory for ``execute``). Added paths are
        searched in the order they were registered, so a module next to the
        importer always wins. Returns the runtime so calls can be chained.
        """
        real = os.path.realpath(path)
        if not os.path.isdir(real):
            raise Errors.RuntimeError(
                f"import path '{path}' is not a directory")
        if real not in self._import_paths:
            self._import_paths.append(real)
        return self

    def execute(self, code: str):
        """Parse and run ``code``.

        Returns the value of the last evaluated expression, or the value of a
        top-level ``return`` if the script uses one.

        ``import "name"`` inside the script resolves against the current
        working directory of the Python process, then against the directories
        added with :meth:`add_import_path`.

        The compiled form of a source is cached, so running the same source
        again skips parsing and compiling it.

        Raises ``Errors.SyntaxError`` if the code cannot be parsed.
        """
        try:
            return self.__interpreter__.run_chunk(self._chunk(code))
        except ThrownSignal as signal:
            raise self.__interpreter__._uncaught(signal) from None

    def _chunk(self, code: str):
        """The compiled chunk of ``code``, compiled once per source."""
        chunk = self._chunks.get(code)
        if chunk is not None:
            return chunk

        chunk = self.__interpreter__.compiler.compile_chunk(self._compile(code))
        if len(self._chunks) >= _CHUNK_CACHE:
            # bounded, so a host that runs many different scripts does not
            # grow the cache without limit
            del self._chunks[next(iter(self._chunks))]
        self._chunks[code] = chunk
        return chunk

    def compile(self, code: str):
        """Compile ``code`` once and return a callable that runs it.

        The returned object can be called with no arguments; it executes the
        already compiled chunk in this runtime.
        """
        chunk = self._chunk(code)

        def run():
            try:
                return self.__interpreter__.run_chunk(chunk)
            except ThrownSignal as signal:
                raise self.__interpreter__._uncaught(signal) from None

        return run

    def _loadcode_host(self, code):
        return self.compile(str(code))

    def execute_module(self, path: str):
        """Execute ``path`` as a Koskript module and return the module.

        The file is resolved against the current working directory, and the
        imports inside it resolve against the directory of the module file.
        Modules are loaded once per runtime and cached; circular imports raise
        ``Errors.RuntimeError``.
        """
        base_dir = os.path.dirname(self._loading[-1]) if self._loading else None
        try:
            return self._load_module(path, base_dir)
        except ThrownSignal as signal:
            raise self.__interpreter__._uncaught(signal) from None

    def _compile(self, code: str):
        """Parse ``code`` into the list of statements the compiler consumes."""
        ast = parse(code)
        if not isinstance(ast, list):
            ast = [ast]
        return ast

    def _module_candidates(self, path: str, base_dir: str) -> list:
        """Absolute paths tried for ``import "path"``, in search order."""
        bases = [None] if os.path.isabs(path) else [base_dir, *self._import_paths]
        candidates = []
        for base in bases:
            candidate = path if base is None else os.path.join(base, path)
            if not candidate.lower().endswith(".kos") \
                    and not os.path.isfile(candidate):
                candidate += ".kos"
            candidates.append(os.path.realpath(candidate))
        return candidates

    def _load_module(self, path: str, base_dir: str = None):
        if base_dir is None:
            base_dir = os.getcwd()

        candidates = self._module_candidates(path, base_dir)
        real = next((item for item in candidates if os.path.isfile(item)), None)
        if real is None:
            looked = ", ".join(f"'{item}'" for item in candidates)
            raise Errors.RuntimeError(
                f"module '{path}' not found (looked for {looked})")

        cached = self._modules.get(real)
        if cached is not None:
            return cached

        if real in self._loading:
            raise Errors.RuntimeError(
                f"circular import of module '{path}'")

        try:
            with open(real, "r", encoding="utf-8-sig") as handle:
                code = handle.read()
        except OSError as e:
            raise Errors.RuntimeError(
                f"cannot read module '{path}': {e}") from e

        try:
            ast = self._compile(code)
        except Errors.SyntaxError as e:
            raise Errors.SyntaxError(f"module '{path}':\n{e}") from None

        interpreter = self.__interpreter__
        info = ScopeInfo(interpreter.root_info)
        scope = Scope(interpreter.root, info)
        name = os.path.splitext(os.path.basename(real))[0]

        self._loading.append(real)
        try:
            interpreter.run_in(ast, scope, info,
                               base_dir=os.path.dirname(real))
        finally:
            self._loading.pop()

        module = Module(name, scope)
        self._modules[real] = module
        return module


def run(code: str, globals_map: dict = None, stdlib: bool = True, **kwargs):
    """One-shot convenience helper.

    >>> run("return 1 + 2")
    3
    """
    merged = dict(globals_map or {})
    merged.update(kwargs)
    return KoskriptRuntime(merged, stdlib=stdlib).execute(code)


__all__ = ["KoskriptRuntime", "KoskriptObject", "Module", "Namespace",
           "Errors", "run", "build_globals"]
