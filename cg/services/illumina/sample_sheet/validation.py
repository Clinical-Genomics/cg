def field_list_elements_validation(attribute: str, value: list[str], name: str) -> list[str]:
    """Validate that the list has two elements and the first element is the expected name."""
    if len(value) != 2:
        raise ValueError(f"{attribute} must have two entries.")
    elif value[0] != name:
        raise ValueError(f"The first entry of {attribute} must be '{name}'.")
    return value


def field_default_value_validation(
    attribute: str, value: list[str], default: list[str]
) -> list[str]:
    """Validate that the value is the default value."""
    if value != default:
        raise ValueError(f"{attribute} must be set to the default value: {default}")
    return value
