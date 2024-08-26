from pathlib import Path

from cg.constants.delivery import INBOX_NAME


def is_inbox_path(file_path: Path):
    return INBOX_NAME in str(file_path)


def get_ticket_dir_path(file_path) -> Path:
    if is_inbox_path(file_path):
        return file_path.parent
