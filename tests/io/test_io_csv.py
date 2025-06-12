from pathlib import Path

import pytest

from cg.io.csv import (
    read_csv,
    read_csv_stream,
    write_csv,
    write_csv_from_dict,
    write_csv_stream,
)
from tests.io.conftest import FileRepresentation


@pytest.mark.parametrize(
    "delimiter",
    [
        ",",
        "\t",
    ],
)
def test_get_content_from_file(delimiter: str, delimiter_map: dict[str, FileRepresentation]):
    """
    Tests reading a file with the given separator.
    """
    # GIVEN a file with the given delimiter
    file_path = delimiter_map[delimiter].filepath

    # WHEN reading the file
    raw_csv_content: list[list[str]] = read_csv(file_path=file_path, delimiter=delimiter)

    # THEN assert a list is returned
    assert isinstance(raw_csv_content, list)

    # THEN all three values in each line should be parsed
    assert all(len(line) == 3 for line in raw_csv_content)


@pytest.mark.parametrize(
    "delimiter",
    [
        ",",
        "\t",
    ],
)
def test_get_content_from_file_to_dict(
    delimiter: str, delimiter_map: dict[str, FileRepresentation]
):
    """
    Tests reading a delimited file into a list of dictionaries.
    """
    # GIVEN a file with the given delimiter
    file_path = delimiter_map[delimiter].filepath

    # WHEN reading the file
    raw_csv_content: list[list[str]] = read_csv(
        file_path=file_path, delimiter=delimiter, read_to_dict=True
    )

    # THEN assert a list is returned and that the first element is a dict
    assert isinstance(raw_csv_content, list)
    assert isinstance(raw_csv_content[0], dict)

    # THEN all three values in each line should be parsed
    assert all(len(line) == 3 for line in raw_csv_content)


@pytest.mark.parametrize(
    "delimiter",
    [
        ",",
        "\t",
    ],
)
def test_get_content_from_stream(delimiter: str, delimiter_map: dict[str, FileRepresentation]):
    """
    Tests reading a delimited stream.
    """
    # GIVEN a string separated by the given delimiter
    stream = delimiter_map[delimiter].content

    # WHEN reading the content in string
    raw_content: list[list[str]] = read_csv_stream(stream=stream, delimiter=delimiter)

    # THEN assert a list is returned
    assert isinstance(raw_content, list)

    # THEN the content should match the expected content
    expected_content = [["Lorem", "ipsum", "sit", "amet"]]
    assert raw_content == expected_content


@pytest.mark.parametrize(
    "delimiter",
    [
        ",",
        "\t",
    ],
)
def test_write_csv(delimiter: str, delimiter_map: dict[str, FileRepresentation]):
    """
    Tests writing content to a file with each delimiter.
    """
    # GIVEN a file with the given delimiter

    # GIVEN a file path to write to
    file_path = delimiter_map[delimiter].filepath
    output_file = delimiter_map[delimiter].output_file
    # WHEN reading the file
    raw_csv_content: list[list[str]] = read_csv(file_path=file_path, delimiter=delimiter)

    # WHEN writing the content
    write_csv(content=raw_csv_content, file_path=output_file, delimiter=delimiter)

    # THEN a file was successfully created
    assert Path.exists(output_file)

    # WHEN reading it again
    written_raw_csv_content: list[list[str]] = read_csv(file_path=output_file, delimiter=delimiter)

    # THEN assert that all data is the same
    assert raw_csv_content == written_raw_csv_content


@pytest.mark.parametrize(
    "delimiter",
    [
        ",",
        "\t",
    ],
)
def test_write_csv_from_dict(delimiter: str, delimiter_map: dict[str, FileRepresentation]):
    """
    Tests writing content to a file with each delimiter.
    """
    # GIVEN a file with the given delimiter

    # GIVEN a file path to write to
    file_path = delimiter_map[delimiter].filepath
    output_file = delimiter_map[delimiter].output_file

    # WHEN reading the file
    raw_csv_content: list[dict] = read_csv(
        file_path=file_path, delimiter=delimiter, read_to_dict=True
    )

    # WHEN writing the content
    write_csv_from_dict(
        content=raw_csv_content,
        file_path=output_file,
        delimiter=delimiter,
        fieldnames=sorted(raw_csv_content[0].keys()),
    )

    # THEN a file was successfully created
    assert Path.exists(output_file)

    # WHEN reading it again
    written_raw_csv_content: list[dict] = read_csv(
        file_path=output_file, delimiter=delimiter, read_to_dict=True
    )

    # THEN assert that all data is the same
    assert raw_csv_content == written_raw_csv_content


@pytest.mark.parametrize(
    "delimiter",
    [
        ",",
        "\t",
    ],
)
def test_write_csv_stream(delimiter: str, delimiter_map: dict[str, FileRepresentation]):
    """
    Tests writing content to a stream with each delimiter.
    """
    # GIVEN a list of lists
    stream = delimiter_map[delimiter].content
    # WHEN writing the stream
    written_stream: str = write_csv_stream(
        content=[["Lorem", "ipsum", "sit", "amet"]], delimiter=delimiter
    )

    # THEN assert that the stream is correct
    assert written_stream == stream + "\n"
