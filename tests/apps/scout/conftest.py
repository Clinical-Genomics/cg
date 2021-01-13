"""Fixtures for the scout api tests"""

from pathlib import Path

import pytest

from cg.apps.scout.scoutapi import ScoutAPI
from tests.mocks.process_mock import ProcessMock


class MockScoutApi(ScoutAPI):
    def __init__(self, config: dict):
        binary_path = "scout"
        config_path = "config_path"
        self.process = ProcessMock(binary=binary_path, config=config_path)


@pytest.fixture(name="sample_dict")
def fixture_sample_dict() -> dict:
    sample_dict = {
        "analysis_type": "wgs",
        "bam_path": "/path/to/sample.bam",
        "mt_bam": "/path/to/reduced_mt.bam",
        "capture_kit": None,
        "father": "0",
        "mother": "0",
        "sample_id": "sample_id",
        "sample_name": "sample_name",
        "sex": "male",
        "tissue_type": "unknown",
        "phenotype": "affected",
    }
    return dict(sample_dict)


@pytest.fixture(name="scout_dir")
def fixture_scout_dir(apps_dir: Path) -> Path:
    """Return the path to the scout fixtures dir"""
    return apps_dir / "scout"


@pytest.fixture(name="causatives_file")
def fixture_causatives_file(scout_dir: Path) -> Path:
    """Return the path to a file with causatives output"""
    return scout_dir / "export_causatives.json"


@pytest.fixture(name="cases_file")
def fixture_cases_file(scout_dir: Path) -> Path:
    """Return the path to a file with export cases output"""
    return scout_dir / "case_export.json"


@pytest.fixture(name="none_case_file")
def fixture_none_case_file(scout_dir: Path) -> Path:
    """Return the path to a file with export cases output where mandatory fields are None"""
    return scout_dir / "none_case_export.json"


@pytest.fixture(name="other_sex_case_file")
def fixture_other_sex_case_file(scout_dir: Path) -> Path:
    """Return the path to a file with export cases output where sex is 'other0'"""
    return scout_dir / "other_sex_case.json"


@pytest.fixture(name="none_case_output")
def fixture_none_case_output(none_case_file: Path) -> str:
    """Return the content of a export causatives run with scout"""
    with open(none_case_file, "r") as infile:
        content = infile.read()
    return content


@pytest.fixture(name="other_sex_case_output")
def fixture_other_sex_case_output(other_sex_case_file: Path) -> str:
    """Return the content of a export causatives run with scout"""
    with open(other_sex_case_file, "r") as infile:
        content = infile.read()
    return content


@pytest.fixture(name="causative_output")
def fixture_causative_output(causatives_file: Path) -> str:
    """Return the content of a export causatives run with scout"""
    with open(causatives_file, "r") as infile:
        content = infile.read()
    return content


@pytest.fixture(name="export_cases_output")
def fixture_export_cases_output(cases_file: Path) -> str:
    """Return the content of a export cases output"""
    with open(cases_file, "r") as infile:
        content = infile.read()
    return content


@pytest.fixture(name="scout_api")
def fixture_scout_api() -> ScoutAPI:
    return MockScoutApi({})
