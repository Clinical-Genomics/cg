from pathlib import Path
from typing import List
from cg.io.csv import read_csv, write_csv, read_csv_stream, write_csv_stream


def test_get_content_from_file(csv_file_path: Path):
    """
    Tests read CSV.
    """
    # GIVEN a csv file

    # WHEN reading the csv file
    raw_csv_content: List[List[str]] = read_csv(file_path=csv_file_path)

    # Then assert a list is returned
    assert isinstance(raw_csv_content, List)


def test_get_content_from_file_to_dict(csv_file_path: Path):
    """
    Tests read CSV into a list of dictionaries.
    """
    # GIVEN a csv file

    # WHEN reading the csv file
    raw_csv_content: List[List[str]] = read_csv(file_path=csv_file_path, read_to_dict=True)

    # Then assert a list is returned and that the first element is a dict
    assert isinstance(raw_csv_content, List)
    assert isinstance(raw_csv_content[0], dict)


def test_get_content_from_stream(csv_stream: str):
    """
    Tests read CSV stream.
    """
    # GIVEN a string in csv format

    # WHEN reading the csv content in string
    raw_content: List[List[str]] = read_csv_stream(stream=csv_stream)

    # THEN assert a list is returned
    assert isinstance(raw_content, List)

    # THEN the content should match the expected content
    expected_content = [["Lorem", "ipsum", "sit", "amet"]]
    assert raw_content == expected_content


def test_write_csv(csv_file_path: Path, csv_temp_path: Path):
    """
    Tests write CSV.
    """
    # GIVEN a csv file

    # GIVEN a file path to write to

    # WHEN reading the csv file
    raw_csv_content: List[List[str]] = read_csv(file_path=csv_file_path)

    # WHEN writing the csv file from dict
    write_csv(content=raw_csv_content, file_path=csv_temp_path)

    # THEN assert that a file was successfully created
    assert Path.exists(csv_temp_path)

    # WHEN reading it as a csv
    written_raw_csv_content: List[List[str]] = read_csv(file_path=csv_temp_path)

    # THEN assert that all data is kept
    assert raw_csv_content == written_raw_csv_content


def test_write_csv_stream(csv_stream: str):
    """
    Tests write CSV stream.
    """
    # GIVEN a list of lists

    # WHEN writing the csv stream
    written_stream: str = write_csv_stream(content=[["Lorem", "ipsum", "sit", "amet"]])

    # THEN assert that the stream is correct
    assert written_stream == csv_stream + "\n"
