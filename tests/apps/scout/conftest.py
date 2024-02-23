"""Fixtures for the scout api tests"""

from pathlib import Path

import pytest

from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants.constants import FileFormat
from cg.constants.pedigree import Pedigree
from cg.constants.subject import PhenotypeStatus, RelationshipStatus, Sex
from cg.io.controller import ReadFile
from cg.models.scout.scout_load_config import Reviewer
from tests.mocks.process_mock import ProcessMock

SCOUT_INDIVIDUAL: dict = {
    "alignment_path": Path("path", "to", "sample.bam").as_posix(),
    "analysis_type": "wgs",
    "capture_kit": None,
    "mitodel_file": Path("path", "to", "mitodel.txt").as_posix(),
    "mt_bam": Path("path", "to", "reduced_mt.bam").as_posix(),
    "reviewer": Reviewer(
        alignment=Path("path", "to", "expansionhunter.bam").as_posix(),
        alignment_index=Path("path", "to", "expansionhunter.bam.bai").as_posix(),
        catalog=Path("path", "to", "variant_catalog.json").as_posix(),
        vcf=Path("path", "to", "expansionhunter.vcf").as_posix(),
    ),
    "sample_id": "sample_id",
    "sample_name": "sample_name",
    "tissue_type": "unknown",
    Pedigree.FATHER: RelationshipStatus.HAS_NO_PARENT,
    Pedigree.MOTHER: RelationshipStatus.HAS_NO_PARENT,
    Pedigree.PHENOTYPE: PhenotypeStatus.AFFECTED,
    Pedigree.SEX: Sex.MALE,
}


class MockScoutApi(ScoutAPI):
    def __init__(self, config: dict):
        binary_path = "scout"
        config_path = "config_path"
        self.process = ProcessMock(binary=binary_path, config=config_path)


@pytest.fixture
def scout_individual() -> dict:
    """Returns a dict template for a ScoutIndividual."""
    return SCOUT_INDIVIDUAL


@pytest.fixture
def omim_disease_nr() -> int:
    return 607208


@pytest.fixture
def scout_dir(apps_dir: Path) -> Path:
    """Return the path to the scout fixtures dir"""
    return Path(apps_dir, "scout")


@pytest.fixture
def causatives_file(scout_dir: Path) -> Path:
    """Return the path to a file with causatives output"""
    return Path(scout_dir, "export_causatives.json")


@pytest.fixture
def cases_file(scout_dir: Path) -> Path:
    """Return the path to a file with export cases output"""
    return Path(scout_dir, "case_export.json")


@pytest.fixture
def none_case_file(scout_dir: Path) -> Path:
    """Return the path to a file with export cases output where mandatory fields are None"""
    return Path(scout_dir, "none_case_export.json")


@pytest.fixture
def other_sex_case_file(scout_dir: Path) -> Path:
    """Return the path to a file with export cases output where sex is 'other0'"""
    return Path(scout_dir, "other_sex_case.json")


@pytest.fixture
def none_case_raw(none_case_file: Path) -> dict:
    """Return a single case of a export causatives run with scout"""
    cases: list = ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=none_case_file
    )
    return cases[0]


@pytest.fixture
def other_sex_case_output(other_sex_case_file: Path) -> str:
    """Return the content of a export causatives run with scout"""
    with open(other_sex_case_file, "r") as infile:
        content = infile.read()
    return content


@pytest.fixture
def causative_output(causatives_file: Path) -> str:
    """Return the content of a export causatives run with scout"""
    with open(causatives_file, "r") as infile:
        content = infile.read()
    return content


@pytest.fixture
def export_cases_output(cases_file: Path) -> str:
    """Return the content of a export cases output"""
    with open(cases_file, "r") as infile:
        content = infile.read()
    return content


@pytest.fixture
def scout_api() -> ScoutAPI:
    return MockScoutApi({})
