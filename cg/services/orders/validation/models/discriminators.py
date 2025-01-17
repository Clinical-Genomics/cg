from typing import Any


def has_internal_id(v: Any) -> str:
    if isinstance(v, dict):
        return "existing" if v.get("internal_id") else "new"
    return "existing" if getattr(v, "internal_id", None) else "new"
