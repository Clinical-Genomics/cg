

def field_not_none(value: str):
    if value is None:
        raise ValueError("Field cannot be None")
    return value
