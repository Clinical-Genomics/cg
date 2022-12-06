"""Fixtures for the scout api tests"""

from pathlib import Path

import pytest

from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants.constants import FileFormat
from cg.constants.pedigree import Pedigree
from cg.constants.subject import Gender, PhenotypeStatus, RelationshipStatus
from cg.io.controller import ReadFile
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
        "bam_path": Path("path", "to", "sample.bam").as_posix(),
        "mt_bam": Path("path", "to", "reduced_mt.bam").as_posix(),
        "reviewer": {
            "alignment": Path("path", "to", "expansionhunter.bam").as_posix(),
            "alignment_index": Path("path", "to", "expansionhunter.bam.bai").as_posix(),
            "vcf": Path("path", "to", "expansionhunter.vcf").as_posix(),
            "catalog": Path("path", "to", "variant_catalog.json").as_posix(),
        },
        "capture_kit": None,
        Pedigree.FATHER: RelationshipStatus.HAS_NO_PARENT,
        Pedigree.MOTHER: RelationshipStatus.HAS_NO_PARENT,
        "sample_id": "sample_id",
        "sample_name": "sample_name",
        Pedigree.SEX: Gender.MALE,
        "tissue_type": "unknown",
        Pedigree.PHENOTYPE: PhenotypeStatus.AFFECTED,
    }
    return dict(sample_dict)


@pytest.fixture(name="omim_disease_nr")
def fixture_omim_disease_nr() -> int:
    return 607208


@pytest.fixture(name="scout_dir")
def fixture_scout_dir(apps_dir: Path) -> Path:
    """Return the path to the scout fixtures dir"""
    return Path(apps_dir, "scout")


@pytest.fixture(name="causatives_file")
def fixture_causatives_file(scout_dir: Path) -> Path:
    """Return the path to a file with causatives output"""
    return Path(scout_dir, "export_causatives.json")


@pytest.fixture(name="cases_file")
def fixture_cases_file(scout_dir: Path) -> Path:
    """Return the path to a file with export cases output"""
    return Path(scout_dir, "case_export.json")


@pytest.fixture(name="none_case_file")
def fixture_none_case_file(scout_dir: Path) -> Path:
    """Return the path to a file with export cases output where mandatory fields are None"""
    return Path(scout_dir, "none_case_export.json")


@pytest.fixture(name="other_sex_case_file")
def fixture_other_sex_case_file(scout_dir: Path) -> Path:
    """Return the path to a file with export cases output where sex is 'other0'"""
    return Path(scout_dir, "other_sex_case.json")


@pytest.fixture(name="none_case_raw")
def fixture_none_case_raw(none_case_file: Path) -> dict:
    """Return a single case of a export causatives run with scout"""
    cases: list = ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=none_case_file
    )
    return cases[0]


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
