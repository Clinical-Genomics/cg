"""Utils related to str manipulation."""


def get_element_from_split(value: str, element_position: int, split: str) -> str:
    return value.split(split)[element_position]
