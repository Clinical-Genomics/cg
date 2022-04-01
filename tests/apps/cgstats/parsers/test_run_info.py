from pathlib import Path

from cg.apps.cgstats.parsers.run_info import RunInfo


def test_parse_run_info(run_info_path: Path):
    """Test if RunInfo parser is working properly and generates information"""
    # GIVEN an existing RunInfo.xml path
    assert run_info_path.exists()

    # WHEN instantiation a RunInfo object
    run_info_obj: RunInfo = RunInfo(run_info_path)

    # THEN the object should be successfully parsed and contain information_sheet
    assert run_info_obj.basemask


def test_run_info_basemask(run_info_path: Path):
    """Test if basemask generation is working as expected"""
    # GIVEN a expected basemask structure
    expected_basemask: str = "51,8,8,51"

    # WHEN generating the basemask from runinfo
    generated_basemask: str = RunInfo(run_info_path).basemask

    # THEN the generated basemask should match the expected one
    assert generated_basemask == expected_basemask
