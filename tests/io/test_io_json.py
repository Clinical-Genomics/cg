from pathlib import Path

from cg.io.json import read_json, write_json, read_json_stream, write_json_stream


def test_get_content_from_file(mip_json_order_form_path: Path):
    """
    Tests read_json
    """
    # GIVEN a json file

    # WHEN reading the json file
    raw_mip_order_form: dict = read_json(file_path=mip_json_order_form_path)

    # Then assert a dict is returned
    assert isinstance(raw_mip_order_form, dict)


def test_get_content_from_stream(json_stream: str):
    """
    Tests read_json_stream
    """
    # GIVEN a string in json format

    # WHEN reading the json content in string
    raw_content: dict = read_json_stream(stream=json_stream)

    # THEN assert a dict is returned
    assert isinstance(raw_content, dict)


def test_write_json(mip_json_order_form_path: Path, cg_dir: Path):
    """
    Tests write_json
    """
    # GIVEN a json file

    # GIVEN a file path to write to
    json_file: Path = Path(cg_dir, "write_json.json")

    # WHEN reading the json file
    raw_mip_order_form: dict = read_json(file_path=mip_json_order_form_path)

    # WHEN writing the json file from dict
    write_json(content=raw_mip_order_form, file_path=json_file)

    # THEN assert that a file was successfully created
    assert Path.exists(json_file)

    # WHEN reading it as a json
    written_raw_mip_order_form: dict = read_json(file_path=json_file)

    # THEN assert that all data is kept
    assert raw_mip_order_form == written_raw_mip_order_form


def test_write_json_stream(json_stream: str):
    """
    Tests write_json_stream
    """
    # GIVEN a list
    raw_content: dict = read_json_stream(stream=json_stream)

    # WHEN writing the list to a json stream
    json_content = write_json_stream(content=raw_content)

    # THEN assert that all data is kept and properly formatted
    assert json_stream == json_content
