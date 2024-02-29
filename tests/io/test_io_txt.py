from pathlib import Path

import pytest

from cg.io.txt import read_txt, write_txt, concat_txt


def test_read_txt_to_list(txt_file_path: Path):
    """
    Test reading content from a TXT file into a list.
    """
    # GIVEN a txt file

    # WHEN reading the file
    content: list[str] = read_txt(file_path=txt_file_path)

    # THEN assert a list is returned
    assert isinstance(content, list)

    # THEN the content should match the expected lines
    expected_lines: list[str] = ["Line 1\n", "Line 2\n", "Line 3"]
    assert content == expected_lines


def test_read_txt_to_string(txt_file_path: Path):
    """
    Test reading content from a TXT file into a string.
    """
    # GIVEN a txt file

    # WHEN reading the file as a string
    content: str = read_txt(file_path=txt_file_path, read_to_string=True)

    # THEN assert a string is returned
    assert isinstance(content, str)

    # THEN the content should match the expected content
    expected_content: str = "Line 1\nLine 2\nLine 3"
    assert content == expected_content


def test_non_existent_file(non_existing_file_path: Path):
    """
    Test handling a non-existent file.
    """
    # GIVEN a path to a non-existing file

    # WHEN attempting to read a non-existent file
    with pytest.raises(FileNotFoundError):
        read_txt(non_existing_file_path)


def test_write_txt(txt_temp_path: Path, txt_file_path: Path):
    """Test writing content to a TXT file."""
    # GIVEN a txt file path to write to

    # GIVEN text content
    content: list[str] = read_txt(file_path=txt_file_path)

    # WHEN writing the file
    write_txt(content=content, file_path=txt_temp_path)

    # THEN assert file exists
    assert txt_temp_path.exists()

    # THEN the content should match the original content
    assert content == read_txt(file_path=txt_temp_path)


def test_concat_txt(txt_file_path: Path, txt_file_path_2: Path, txt_temp_path: Path):
    """Test concatenating two files, no optional string content"""
    # GIVEN a list of file paths to concatenate

    # WHEN concatenating two files
    concat_txt(
        file_paths=[txt_file_path, txt_file_path_2], target_file=txt_temp_path, str_content=None
    )

    # THEN the target file should exist
    assert txt_temp_path.exists()


def test_concat_txt_with_string(
    txt_file_path: Path, txt_file_path_2: Path, txt_temp_path: Path, csv_stream: str
):
    """Test concatenating two files, no optional string content"""
    # GIVEN a list of file paths to concatenate

    # WHEN concatenating two files
    concat_txt(
        file_paths=[txt_file_path, txt_file_path_2],
        target_file=txt_temp_path,
        str_content=[csv_stream],
    )

    # THEN the target file should exist
    assert txt_temp_path.exists()

    # THEN the content should match the input string
    assert read_txt(file_path=txt_temp_path) == [
        "Lorem,ipsum,sit,amet\n",
        "Line 1\n",
        "Line 2\n",
        "Line 3\n",
        "Line 4\n",
        "Line 5\n",
        "Line 6\n",
    ]
