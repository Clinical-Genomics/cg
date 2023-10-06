from pathlib import Path

from cg.io.yaml import read_yaml, read_yaml_stream, write_yaml, write_yaml_stream
from cg.models.mip.mip_sample_info import MipBaseSampleInfo


def test_get_content_from_file(case_qc_sample_info_path: Path):
    """
    Tests read_yaml
    """
    # GIVEN a yaml file

    # WHEN reading the yaml file
    raw_sample_info: dict = read_yaml(file_path=case_qc_sample_info_path)

    # Then assert a dict is returned
    assert isinstance(raw_sample_info, dict)

    # WHEN instantiating a MipBaseSampleInfo object
    sample_info_object = MipBaseSampleInfo(**raw_sample_info)

    # THEN assert that it was successfully created
    assert isinstance(sample_info_object, MipBaseSampleInfo)


def test_get_content_from_stream(yaml_stream: str):
    """
    Tests read_yaml_stream
    """
    # GIVEN a string in yaml format

    # WHEN reading the yaml content in string
    raw_content: list = read_yaml_stream(stream=yaml_stream)

    # THEN assert a list is returned
    assert isinstance(raw_content, list)


def test_write_yaml(case_qc_sample_info_path: Path, cg_dir: Path):
    """
    Tests write_yaml
    """
    # GIVEN a yaml file

    # GIVEN a file path to write to
    yaml_file: Path = Path(cg_dir, "write_yaml.yaml")

    # WHEN reading the yaml file
    raw_sample_info: dict = read_yaml(file_path=case_qc_sample_info_path)

    # WHEN writing the yaml file from dict
    write_yaml(content=raw_sample_info, file_path=yaml_file)

    # THEN assert that a file was successfully created
    assert Path.exists(yaml_file)

    # WHEN reading it as a yaml
    written_raw_sample_info: dict = read_yaml(file_path=yaml_file)

    # THEN assert that all data is kept
    assert raw_sample_info == written_raw_sample_info


def test_write_yaml_stream(yaml_stream: str):
    """
    Tests write_yaml_stream
    """
    # GIVEN a list
    raw_content: list = read_yaml_stream(stream=yaml_stream)

    # WHEN writing the list to a yaml stream
    yaml_content = write_yaml_stream(content=raw_content)

    # THEN assert that all data is kept and properly formatted
    assert yaml_stream == yaml_content
