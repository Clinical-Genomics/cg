from cg.utils.files import get_file_in_directory
from pathlib import Path


def test_get_file_in_directory(nested_directory_with_file: Path, some_file: str):
    """Test function to get a file in a directory and subdirectories."""
    # GIVEN a directory with subdirectories with a file
    # WHEN getting the file
    file_path: Path = get_file_in_directory(nested_directory_with_file, some_file)
    # THEN assert that the file is returned
    assert file_path.exists()
