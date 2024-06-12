from datetime import datetime
from pathlib import Path

import pytest

from cg.utils.files import (
    get_directories_in_path,
    get_source_creation_time_stamp,
    get_file_in_directory,
    remove_directory_and_contents,
    rename_file,
    get_files_in_directory_with_pattern,
)


def test_get_file_in_directory(nested_directory_with_file: Path, some_file: str):
    """Test function to get a file in a directory and subdirectories."""
    # GIVEN a directory with subdirectories with a file

    # WHEN getting the file
    file_path: Path = get_file_in_directory(nested_directory_with_file, some_file)

    # THEN assert that the file is returned
    assert file_path.exists()


def test_get_files_in_directory_by_pattern(nested_directory_with_file: Path, some_file: str):
    """Test function to get files with a pattern in a directory and subdirectories."""
    # GIVEN a directory with subdirectories with a file

    # WHEN getting the file
    file_paths: list[Path] = get_files_in_directory_with_pattern(
        directory=nested_directory_with_file, pattern=some_file
    )

    # THEN assert that the file is returned
    for file_path in file_paths:
        assert file_path.exists()
        assert some_file in file_path.as_posix()


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


def test_get_creation_date_for_dir(tmp_path_factory):
    """Test to retrieve the creation date of a directory."""

    # GIVEN a directory that is created now
    directory_path: Path = tmp_path_factory.mktemp("some_dir")

    # WHEN retrieving the creation time stamp
    creation_time_stamp: float = get_source_creation_time_stamp(directory_path)

    # THEN the creation time stamp is returned
    assert isinstance(creation_time_stamp, float)


def test_get_creation_date_for_file(tmp_path_factory):
    """Test to retrieve the creation date of a directory."""

    # GIVEN a file that is created now
    directory_path: Path = tmp_path_factory.mktemp("some_dir")
    file_path: Path = Path(directory_path, "some_file")
    file_path.touch()

    # WHEN retrieving the creation time stamp
    creation_time_stamp: float = get_source_creation_time_stamp(file_path)

    # THEN the creation time stamp is returned
    assert isinstance(creation_time_stamp, float)


def test_get_all_directories_in_path(
    path_with_directories_and_a_file: Path, sub_dir_names: list[str], some_file: str
):
    """Test that get all directories in path only returns directories."""

    # GIVEN a path that contains directories and a file
    assert Path(path_with_directories_and_a_file, some_file).exists()

    # WHEN retrieving all directories in the path
    directories: list[Path] = get_directories_in_path(path=path_with_directories_and_a_file)

    # THEN all directories are returned
    for sub_dir_name in sub_dir_names:
        assert sub_dir_name in [directory.name for directory in directories]

    # THEN no files are returned
    assert some_file not in [directory.name for directory in directories]


def test_remove_directory_and_contents(path_with_directories_and_a_file: Path, some_file: str):
    """Test to remove a directory and all its contents."""

    # GIVEN a path to a directory
    assert path_with_directories_and_a_file.exists()

    # WHEN removing the directory
    remove_directory_and_contents(path_with_directories_and_a_file)

    # THEN the directory and its contents should no longer exist
    assert not path_with_directories_and_a_file.exists()
    assert not Path(path_with_directories_and_a_file, some_file).exists()
