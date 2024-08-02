def find_line_containing_pattern(content: list[list[str]], pattern: str) -> int:
    """
    Find the line in the content that contains a pattern.
    Raises:
        ValueError: if the pattern is not found in the content.
    """
    for index, line in enumerate(content):
        if pattern in line:
            return index
    raise ValueError(f"Pattern {pattern} not found in content")


def is_dual_index(index: str) -> bool:
    """Determines if an index in the raw sample sheet is dual index or not."""
    return "-" in index
