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


def divide_file_content_into_sections(content: list[list[str]], divider_idx: int) -> tuple:
    """
    Divide the content of a file into two sections.
    Raises:
        ValueError: if the divider index is out of bounds.
    """
    if divider_idx < 0:
        raise ValueError(f"Divider index {divider_idx} is out of bounds")
    return content[:divider_idx], content[divider_idx:]
