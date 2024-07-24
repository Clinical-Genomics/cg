"""Utils related to string manipulation."""

from cg.exc import CgError


def get_element_from_split(value: str, element_position: int, split: str) -> str:
    elements: list[str] = value.split(split)
    if len(elements) < element_position:
        raise CgError(message="Provided element position out of bounds.")
    return elements[element_position]
