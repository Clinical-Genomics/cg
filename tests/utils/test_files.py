from cg.utils.files import get_file_in_directory, rename_file
from pathlib import Path
import pytest


def test_get_file_in_directory(nested_directory_with_file: Path, some_file: str):
    """Test function to get a file in a directory and subdirectories."""
    # GIVEN a directory with subdirectories with a file
    # WHEN getting the file
    file_path: Path = get_file_in_directory(nested_directory_with_file, some_file)
    # THEN assert that the file is returned
    assert file_path.exists()


def test_rename_file(tmp_path: Path):
    # GIVEN a file path and a renamed file path
    file_path: Path = Path(tmp_path, "dummy_path")
    renamed_file_path: Path = Path(tmp_path, "dummy_renamed_path")

    # GIVEN that the file path exist
    file_path.touch()
    assert file_path.exists()

    # GIVEN that the renamed file path does not exist
    assert not renamed_file_path.exists()

    # WHEN renaming the file
    rename_file(file_path=file_path, renamed_file_path=renamed_file_path)

    # THEN the renamed file path should exist
    assert renamed_file_path.exists()

    # THEN the file path should not exist
    assert not file_path.exists()


def test_rename_file_exists(tmp_path: Path):
    # GIVEN a file path and a renamed file path
    file_path: Path = Path(tmp_path, "dummy_path")
    renamed_file_path: Path = Path(tmp_path, "dummy_renamed_path")

    # GIVEN that the file path exist
    file_path.touch()
    renamed_file_path.touch()
    assert renamed_file_path.exists()

    # WHEN renaming the file
    rename_file(file_path=file_path, renamed_file_path=renamed_file_path)

    # THEN the renamed file path should exist
    assert renamed_file_path.exists()


def test_rename_file_original_does_not_exist(tmp_path: Path):
    # GIVEN a file path and a renamed file path

    file_path: Path = Path(tmp_path, "dummy_path")
    renamed_file_path: Path = Path(tmp_path, "dummy_renamed_path")

    # GIVEN that the file path does not exist
    assert not file_path.exists()

    # WHEN renaming the file
    # THEN a FileNotFoundError should be raised
    with pytest.raises(FileNotFoundError):
        rename_file(file_path=file_path, renamed_file_path=renamed_file_path)
