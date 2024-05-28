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


def get_files_in_directory_with_pattern(directory: Path, pattern: str) -> list[Path]:
    """Get files with a pattern in a directory and subdirectories.
    Raises:
        FileNotFoundError: If no files with the pattern can be found.
    """
    files_with_pattern: list[Path] = []
    if not directory.is_dir() or not directory.exists():
        raise FileNotFoundError(f"Directory {directory} does not exist")
    for directory_path, _, files in os.walk(directory):
        for file in files:
            if pattern in file:
                files_with_pattern.append(Path(directory_path, file))
    if not files_with_pattern:
        raise FileNotFoundError(f"No files with pattern {pattern} found in {directory}")
    return files_with_pattern


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


def get_source_creation_time_stamp(source_path: Path) -> float:
    """
    Return time stamp that a source is created.
    Raises:
        FileNotFoundError if the source does not exist.
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Directory with path {source_path} is not found.")
    return os.stat(source_path).st_ctime


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


def link_or_overwrite_file(src: Path, dst: Path) -> None:
    """Copy a file from src to dst, overwriting the destination if it exists."""
    if dst.exists():
        LOG.warning(f"{dst} already exists. Overwriting with {src}")
        dst.unlink()
    os.link(src=src, dst=dst)
    LOG.debug(f"Linked {src} to {dst}")
