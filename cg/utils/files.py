"""Some helper functions for working with files"""
import logging
import os
import shutil
from pathlib import Path

LOG = logging.getLogger(__name__)


def get_file_in_directory(directory: Path, file_name: str) -> Path:
    """Get a file in a directory and subdirectories.
    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    if not directory.is_dir() or not directory.exists():
        raise FileNotFoundError(f"Directory {directory} does not exist")
    for directory_path, _, files in os.walk(directory):
        for file in files:
            if file_name == file:
                path_to_file = Path(directory_path, file)
                return path_to_file
    raise FileNotFoundError(f"File {file_name} not found in {directory}")


def get_files_matching_pattern(directory: Path, pattern: str) -> list[Path]:
    """Search for all files in a directory that match a pattern."""
    return list(directory.glob(pattern))


def get_all_files_in_dir(base_path: Path) -> set[Path]:
    """Get a set of all files relative to the given base path."""
    return {file.relative_to(base_path) for file in base_path.rglob("*") if file.is_file()}


def rename_file(file_path: Path, renamed_file_path: Path) -> None:
    """Rename the given file path."""
    file_path.rename(renamed_file_path)
    LOG.debug(f"Renamed {file_path} to {renamed_file_path}.")


def is_pattern_in_file_path_name(file_path: Path, pattern: str) -> bool:
    """Check if a pattern is in a file path."""
    return pattern in file_path.name


def get_directory_creation_time_stamp(directory_path: Path) -> float:
    """
    Return time stamp that a directory is created.
    Raises:
        FileNotFoundError if the directory does not exist.
        ValueError if the specified path is not a directory.
    """
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory with path {directory_path} is not found.")

    if not directory_path.is_dir():
        raise ValueError(f"Specified path {directory_path} is not a directory.")

    return os.stat(directory_path).st_ctime


def remove_directory_and_contents(directory_path):
    """
    Delete a directory and its contents.
    Raises OSError when failed to remove directory.
    """
    try:
        shutil.rmtree(directory_path)
        LOG.info(f"Successfully removed the directory and its contents: {directory_path}")
    except Exception as error:
        raise OSError(f"Failed to remove the directory {directory_path} and its contents: {error}")


def get_directories_in_path(path: Path) -> list[Path]:
    """Get all directories for a specified path.
    Raises FileNotFoundError if the path does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Path {path} does not exist.")
    return [entry for entry in path.iterdir() if entry.is_dir()]
