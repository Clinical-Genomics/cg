from pathlib import Path

from cg.services.post_processing.exc import (
    PostProcessingFileNotFoundError,
    PostProcessingRunValidationError,
)


def validate_name_pre_fix(run_name: str) -> None:
    if not run_name.startswith("r"):
        raise PostProcessingRunValidationError


def validate_has_expected_parts(run_name: str, expected_parts: int) -> None:
    if len(run_name.split("/")) != expected_parts:
        raise PostProcessingRunValidationError


def validate_files_exist(files: list[Path]) -> None:
    """Validate that all files in the list exist."""
    for file in files:
        if not file.exists():
            raise PostProcessingFileNotFoundError(f"File {file.as_posix()} does not exist")
