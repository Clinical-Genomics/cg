from pathlib import Path

from cg.constants.constants import FileFormat
from cg.io.base import ReadFile, WriteFile
from cg.models.mip.mip_sample_info import MipBaseSampleInfo


def test_get_dict_from_file(case_qc_sample_info_path: Path):
    """
    Tests get_dict_from_file
    """
    # GIVEN a yaml file

    # WHEN reading the yaml file
    raw_sample_info: dict = ReadFile.get_dict_from_file(
        ReadFile, file_format=FileFormat.YAML, file_path=case_qc_sample_info_path
    )

    # Then assert a dict is returned
    assert isinstance(raw_sample_info, dict)

    # WHEN instantiating a MipBaseSampleInfo object
    sample_info_object = MipBaseSampleInfo(**raw_sample_info)

    # THEN assert that it was successfully created
    assert isinstance(sample_info_object, MipBaseSampleInfo)


def test_write_file_from_dict(case_qc_sample_info_path: Path, cg_dir: Path):
    """
    Tests write_file_from_dict
    """
    # GIVEN a yaml file

    # GIVEN a file path to write to
    yaml_file: Path = Path(cg_dir, "write_yaml.yaml")

    # WHEN reading the yaml file
    raw_sample_info: dict = ReadFile.get_dict_from_file(
        ReadFile, file_format=FileFormat.YAML, file_path=case_qc_sample_info_path
    )

    # WHEN writing the yaml file from dict
    WriteFile.write_file_from_dict(
        WriteFile, content=raw_sample_info, file_format=FileFormat.YAML, file_path=yaml_file
    )

    # THEN assert that a file was successfully created
    assert Path.exists(yaml_file)

    # WHEN reading it as a yaml
    written_raw_sample_info: dict = ReadFile.get_dict_from_file(
        ReadFile, file_format=FileFormat.YAML, file_path=yaml_file
    )

    # THEN assert that all data is kept
    assert raw_sample_info == written_raw_sample_info
