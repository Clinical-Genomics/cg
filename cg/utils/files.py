"""Some helper functions for working with files"""
from pathlib import Path
from typing import Optional
import os


def get_file_in_directory(directory: Path, file_name: str) -> Path:
    """Get a file in a directory and subdirectories."""
    """Get a file in a directory and subdirectories."""
    if not directory.is_dir() or not directory.exists():
        raise FileNotFoundError(f"Directory {directory} does not exist")
    path_to_file: Optional[Path] = None
    for directory_path, _, files in os.walk(directory):
        for file in files:
            if file_name in file:
                path_to_file = Path(directory_path, file)
                return path_to_file
    if not path_to_file:
        raise FileNotFoundError(f"File {file_name} not found in {directory}")
