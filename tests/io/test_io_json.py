from pathlib import Path

from cg.io.json import read_json, read_json_stream, write_json, write_json_stream


def test_get_content_from_file(json_file_path: Path):
    """
    Tests read_json
    """
    # GIVEN a json file

    # WHEN reading the json file
    raw_json_content: dict = read_json(file_path=json_file_path)

    # Then assert a dict is returned
    assert isinstance(raw_json_content, dict)


def test_get_content_from_stream(json_stream: str):
    """
    Tests read_json_stream
    """
    # GIVEN a string in json format

    # WHEN reading the json content in string
    raw_content: dict = read_json_stream(stream=json_stream)

    # THEN assert a dict is returned
    assert isinstance(raw_content, dict)


def test_write_json(json_file_path: Path, json_temp_path: Path):
    """
    Tests write_json
    """
    # GIVEN a json file

    # GIVEN a file path to write to

    # WHEN reading the json file
    raw_json_content: dict = read_json(file_path=json_file_path)

    # WHEN writing the json file from dict
    write_json(content=raw_json_content, file_path=json_temp_path)

    # THEN assert that a file was successfully created
    assert Path.exists(json_temp_path)

    # WHEN reading it as a json
    written_raw_json_content: dict = read_json(file_path=json_temp_path)

    # THEN assert that all data is kept
    assert raw_json_content == written_raw_json_content


def test_write_json_stream(json_stream: str):
    """
    Tests write_json_stream
    """
    # GIVEN a dict
    raw_content: dict = read_json_stream(stream=json_stream)

    # WHEN writing the dict to a json stream
    json_content = write_json_stream(content=raw_content)

    # THEN assert that all data is kept and properly formatted
    assert json_stream == json_content
