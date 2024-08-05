import re

import click

import shutil


def echo_lines(lines: list[str]) -> None:
    for line in lines:
        click.echo(line)


def is_case_name_allowed(name: str) -> bool:
    """Returns true if the given name consists only of letters, numbers and dashes."""
    allowed_pattern: re.Pattern = re.compile("^[A-Za-z0-9-]+$")
    return bool(allowed_pattern.fullmatch(name))


CLICK_CONTEXT_SETTINGS: dict[str, int] = {
    "max_content_width": shutil.get_terminal_size().columns - 10
}
