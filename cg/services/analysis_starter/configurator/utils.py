from pathlib import Path

import rich_click as click

from cg.io.txt import write_txt


def write_content_to_file_or_stdout(content: str, file_path: Path, dry_run: bool = False) -> None:
    """Write content to a file if dry-run is False, otherwise print to stdout."""
    if dry_run:
        click.echo(content)
        return
    write_txt(content=content, file_path=file_path)
