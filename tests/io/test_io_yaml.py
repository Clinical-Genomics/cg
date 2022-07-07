from pathlib import Path

from cg.io.yaml import read_yaml, write_yaml
from cg.models.mip.mip_sample_info import MipBaseSampleInfo


def test_get_dict_from_file(case_qc_sample_info_path: Path):
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
