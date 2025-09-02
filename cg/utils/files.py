"""Some helper functions for working with files."""

import logging
import os
import shutil
from importlib.resources import files
from pathlib import Path

LOG = logging.getLogger(__name__)


def get_project_root_dir() -> Path:
    return Path(files("cg"))


def get_file_in_directory(directory: Path, file_name: str) -> Path:
    """Get a file in a directory and subdirectories.
    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    if not directory.is_dir() or not directory.exists():
        raise FileNotFoundError(f"Directory {directory} does not exist")
    for directory_path, _, dir_files in os.walk(directory):
        for file in dir_files:
            if file_name == file:
                return Path(directory_path, file)
    raise FileNotFoundError(f"File {file_name} not found in {directory}")


def get_file_with_pattern_from_list(files: list[Path], pattern: str) -> Path | None:
    """
    Return the path whose name matches a pattern from a list of paths.
    Raises:
        FileNotFoundError: If no file matches the pattern.
    """
    for file in files:
        if pattern in file.name:
            return file
    raise FileNotFoundError(f"No {pattern} file found in given file list")


def get_files_matching_pattern(directory: Path, pattern: str) -> list[Path]:
    """Search for all files in a directory that match a pattern."""
    return list(directory.glob(pattern))


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


def get_all_files_in_directory_tree(directory: Path) -> list[Path]:
    """Get the relative paths of all files in a directory and its subdirectories."""
    files_in_directory: list[Path] = []
    for subdir, _, dir_files in os.walk(directory):
        subdir = Path(subdir).relative_to(directory)
        files_in_directory.extend([Path(subdir, file) for file in dir_files])
    return files_in_directory


def get_source_modified_time_stamp(source_path: Path) -> float:
    """
    Return time stamp that a source is modified. Works for files and directories.
    Raises:
        FileNotFoundError if the source does not exist.
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Directory with path {source_path} is not found.")
    return os.stat(source_path).st_mtime
