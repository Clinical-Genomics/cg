"""Module to read or write txt files."""

from pathlib import Path


def read_txt(file_path: Path, read_to_string: bool = False) -> list[str] | str:
    """Read content in a TXT file."""
    with open(file_path, "r") as file:
        if read_to_string:
            return file.read()
        return list(file)


def write_txt(content: list[str], file_path: Path) -> None:
    """Write content to a text file."""
    with open(file_path, "w") as file:
        file.writelines(content)

def concat_txt(file_paths: list[Path], target_file: Path, str_content: str = "") -> None:
    """Concatenate files and eventual string content"""
    content = str_content
    for file_path in file_paths:
        content = content + read_txt(file_path)
    write_txt(content, target_file)
