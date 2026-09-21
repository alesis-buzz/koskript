from . import core, maps


def build_globals() -> dict:
    """Return a fresh set of standard library globals."""
    globals_map = {}
    globals_map.update(core.build())
    globals_map.update(maps.build())
    return globals_map


__all__ = ["build_globals"]
