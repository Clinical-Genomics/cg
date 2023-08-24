"""Some helper functions for working with files"""
from pathlib import Path
import os
from typing import List, Set


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


def get_files_matching_pattern(directory: Path, pattern: str) -> List[Path]:
    """Search for all files in a directory that match a pattern."""
    return list(directory.glob(pattern))


def get_all_files_in_dir(base_path: Path) -> Set[Path]:
    """Get a set of all files relative to the given base path."""
    return {file.relative_to(base_path) for file in base_path.rglob("*") if file.is_file()}
