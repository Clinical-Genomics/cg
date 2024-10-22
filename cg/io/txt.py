"""Module to read or write txt files."""

import logging
from pathlib import Path

from cg.constants.symbols import EMPTY_STRING

LOG = logging.getLogger(__name__)


def read_txt(file_path: Path, read_to_string: bool = False) -> list[str] | str:
    """Read content in a TXT file."""
    with open(file_path, "r") as file:
        if read_to_string:
            return file.read()
        return list(file)


def write_txt(content: list[str] | str, file_path: Path) -> None:
    """Write content to a text file."""
    with open(file_path, "w") as file:
        if isinstance(content, list):
            file.writelines(content)
        else:
            file.write(content)


def concat_txt(
    file_paths: list[Path | str],
    str_content: list[str] | None = None,
) -> str | None:
    """Concatenate the content of several files and eventual string content."""
    LOG.debug("Concatenate config files")
    content: str = EMPTY_STRING
    if str_content:
        LOG.debug(f"{str_content}")
        for txt in str_content:
            content += f"{txt}\n"
    for file_path in file_paths:
        LOG.debug(f"{file_path}")
        file_content: str = read_txt(file_path, read_to_string=True)
        content += f"{file_content}\n"
        LOG.debug(f"{content}")
    LOG.debug(f"{content}")
    return content
