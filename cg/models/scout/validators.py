def field_not_none(value: str):
    if not value:
        raise ValueError("Field cannot be None")
    return value
