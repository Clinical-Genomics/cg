import logging
from pathlib import Path

LOG = logging.getLogger(__name__)


def validate_name_pre_fix(run_name: str, pre_fix: str) -> None:
    if not run_name.startswith(pre_fix):
        raise ValueError(f"Run name does not start with {pre_fix}")


def validate_has_expected_parts(run_name: str, expected_parts: int) -> None:
    if len(run_name.split("/")) != expected_parts:
        raise ValueError(f"Run name does not have number of expected parts {expected_parts}.")


def validate_files_or_directories_exist(files: list[Path]) -> None:
    """Validate that all files or directories in the list exist."""
    exit_success: bool = True
    for file in files:
        if not file.exists():
            LOG.error(f"File or directory {file.as_posix()} does not exist")
            exit_success = False
    if not exit_success:
        raise FileNotFoundError("Some of the provided paths do not exist")
