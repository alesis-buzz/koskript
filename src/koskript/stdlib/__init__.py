from . import arrays, core, jsonlib, mathlib, maps, strings


def build_globals(call_value=None) -> dict:
    """Return a fresh set of standard library globals."""
    globals_map = {}
    globals_map.update(core.build())
    globals_map.update(maps.build())
    globals_map.update(arrays.build(call_value))
    globals_map.update(strings.build())
    globals_map.update(mathlib.build())
    globals_map.update(jsonlib.build())
    return globals_map


__all__ = ["build_globals"]
