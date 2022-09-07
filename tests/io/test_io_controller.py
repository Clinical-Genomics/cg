from pathlib import Path

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile, WriteFile, ReadStream, WriteStream
from cg.models.mip.mip_sample_info import MipBaseSampleInfo


def test_get_content_from_file(case_qc_sample_info_path: Path):
    """
    Tests get_content_from_file
    """
    # GIVEN a yaml file

    # WHEN reading the yaml file
    raw_sample_info: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML, file_path=case_qc_sample_info_path
    )

    # Then assert a dict is returned
    assert isinstance(raw_sample_info, dict)

    # WHEN instantiating a MipBaseSampleInfo object
    sample_info_object = MipBaseSampleInfo(**raw_sample_info)

    # THEN assert that it was successfully created
    assert isinstance(sample_info_object, MipBaseSampleInfo)


def test_get_content_from_file_when_json(json_file_path: Path):
    """
    Tests get_content_from_file when json
    """
    # GIVEN a json file

    # WHEN reading the json file
    raw_json_content: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=json_file_path
    )

    # Then assert a dict is returned
    assert isinstance(raw_json_content, dict)


def test_get_content_from_stream(yaml_stream: str):
    """
    Tests read_yaml_stream
    """
    # GIVEN a string in yaml format

    # WHEN reading the yaml content in string
    raw_content: list = ReadStream.get_content_from_stream(
        file_format=FileFormat.YAML, stream=yaml_stream
    )

    # THEN assert that a list is returned
    assert isinstance(raw_content, list)


def test_get_content_from_stream_when_json(json_stream: str):
    """
    Tests read_json_stream
    """
    # GIVEN a string in json format

    # WHEN reading the json content in string
    raw_content: dict = ReadStream.get_content_from_stream(
        file_format=FileFormat.JSON, stream=json_stream
    )

    # THEN assert that a dict is returned
    assert isinstance(raw_content, dict)


def test_write_file_from_content(case_qc_sample_info_path: Path, cg_dir: Path):
    """
    Tests write_file_from_content
    """
    # GIVEN a yaml file

    # GIVEN a file path to write to
    yaml_file: Path = Path(cg_dir, "write_yaml.yaml")

    # WHEN reading the yaml file
    raw_sample_info: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML, file_path=case_qc_sample_info_path
    )

    # WHEN writing the yaml file from dict
    WriteFile.write_file_from_content(
        content=raw_sample_info, file_format=FileFormat.YAML, file_path=yaml_file
    )

    # THEN assert that a file was successfully created
    assert Path.exists(yaml_file)

    # WHEN reading it as a yaml
    written_raw_sample_info: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML, file_path=yaml_file
    )

    # THEN assert that all data is kept
    assert raw_sample_info == written_raw_sample_info


def test_write_file_from_content_when_json(json_file_path: Path, json_temp_path: Path):
    """
    Tests write_file_from_content when json
    """
    # GIVEN a json file

    # GIVEN a file path to write to

    # WHEN reading the json file
    raw_json_content: list = ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=json_file_path
    )

    # WHEN writing the json file from list
    WriteFile.write_file_from_content(
        content=raw_json_content, file_format=FileFormat.JSON, file_path=json_temp_path
    )

    # THEN assert that a file was successfully created
    assert Path.exists(json_temp_path)

    # WHEN reading it as a yaml
    written_raw_sample_info: list = ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=json_temp_path
    )

    # THEN assert that all data is kept
    assert raw_json_content == written_raw_sample_info


def test_write_yaml_stream_from_content(yaml_stream: str):
    """
    Tests read_yaml_stream
    """
    # GIVEN a string in yaml format

    # WHEN reading the yaml content in string
    raw_content: list = ReadStream.get_content_from_stream(
        file_format=FileFormat.YAML, stream=yaml_stream
    )
    # WHEN writing a yaml stream
    yaml_content = WriteStream.write_stream_from_content(
        content=raw_content, file_format=FileFormat.YAML
    )

    # THEN assert all data is kept abd in yaml format
    assert yaml_stream == yaml_content


def test_write_json_stream_from_content(json_stream: str):
    """
    Tests read_json_stream
    """
    # GIVEN a string in json format

    # WHEN reading the json content in string
    raw_content: list = ReadStream.get_content_from_stream(
        file_format=FileFormat.JSON, stream=json_stream
    )
    # WHEN writing a json stream
    json_content = WriteStream.write_stream_from_content(
        content=raw_content, file_format=FileFormat.JSON
    )

    # THEN assert all data is kept abd in json format
    assert json_stream == json_content
