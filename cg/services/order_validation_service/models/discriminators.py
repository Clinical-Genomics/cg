from typing import Any


def has_internal_id(v: Any) -> str:
    if isinstance(v, dict):
        return "existing" if "internal_id" in v.keys() else "new"
    return "existing" if getattr(v, "internal_id", None) else "new"
