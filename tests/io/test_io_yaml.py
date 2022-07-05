from pathlib import Path
from typing import Dict

from cg.io.yaml import read_yaml
from cg.models.mip.mip_sample_info import MipBaseSampleInfo


def test_read_yaml(case_qc_sample_info_path: Path):
    """
    Tests read_yaml
    """
    # GIVEN a config file handle

    # WHEN reading and parsing the yaml file
    raw_sample_info: Dict = read_yaml(file_path=case_qc_sample_info_path)

    # Then assert a dict is returned
    assert isinstance(raw_sample_info, Dict)

    # WHEN instantiating a MipBaseSampleInfo object
    sample_info_object = MipBaseSampleInfo(**raw_sample_info)

    # THEN assert that it was successfully created
    assert isinstance(sample_info_object, MipBaseSampleInfo)
