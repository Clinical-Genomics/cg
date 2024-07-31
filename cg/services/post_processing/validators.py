from pathlib import Path


def validate_name_pre_fix(run_name: str, pre_fix: str) -> None:
    if not run_name.startswith(pre_fix):
        raise ValueError(f"Run name does not start with {pre_fix}")


def validate_has_expected_parts(run_name: str, expected_parts: int) -> None:
    if len(run_name.split("/")) != expected_parts:
        raise ValueError(f"Run name does not have number of expected parts {expected_parts}.")


def validate_files_exist(files: list[Path]) -> None:
    """Validate that all files in the list exist."""
    for file in files:
        if not file.exists():
            raise FileNotFoundError(f"File {file.as_posix()} does not exist")
