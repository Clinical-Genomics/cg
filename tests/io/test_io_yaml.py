from pathlib import Path

from cg.io.yaml import read_yaml
from cg.models.mip.mip_sample_info import MipBaseSampleInfo


def test_read_yaml(case_qc_sample_info_path: Path):
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
