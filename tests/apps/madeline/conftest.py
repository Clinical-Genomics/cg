"""Fixtures for testing the madeline cg app"""

from pathlib import Path

import pytest

from cg.apps.madeline.api import MadelineAPI
from tests.mocks.process_mock import ProcessMock


@pytest.fixture
def madeline_output(apps_dir: Path) -> Path:
    """Path to madeline output"""
    return apps_dir / "madeline" / "madeline.xml"


@pytest.fixture
def madeline_columns() -> dict[str, str]:
    """return a dictionary with madeline columns"""
    columns = {
        "case": "FamilyId",
        "sample": "IndividualId",
        "sex": "Gender",
        "father": "Father",
        "mother": "Mother",
        "deceased": "Deceased",
        "proband": "Proband",
        "status": "Affected",
    }
    return columns


@pytest.fixture
def mother() -> dict[str, str | None]:
    """return a dictionary with ind info"""
    ind_info = {
        "sample": "mother",
        "sex": "female",
        "proband": False,
        "status": "unaffected",
    }
    return ind_info


@pytest.fixture
def father() -> dict[str, str | None]:
    """return a dictionary with ind info"""
    ind_info = {
        "sample": "father",
        "sex": "male",
        "proband": False,
        "status": "unaffected",
    }
    return ind_info


@pytest.fixture
def proband() -> dict[str, str | None]:
    """return a dictionary with ind info"""
    ind_info = {
        "sample": "proband",
        "sex": "female",
        "father": "father",
        "mother": "mother",
        "deceased": False,
        "proband": True,
        "status": "affected",
    }
    return ind_info


@pytest.fixture
def trio(proband: dict, mother: dict, father: dict) -> list[dict[str, str | None]]:
    """return a list with a trio"""
    return [proband, mother, father]


@pytest.fixture
def madeline_api() -> MadelineAPI:
    """Return a madeline API with mocked process"""
    binary_path = "madeline"
    config = {"madeline_exe": binary_path}
    madeline_api: MadelineAPI = MadelineAPI(config)
    madeline_process: ProcessMock = ProcessMock(binary=binary_path)
    madeline_api.process = madeline_process
    return madeline_api


@pytest.fixture
def populated_madeline_api(madeline_output: Path, madeline_api: MadelineAPI) -> MadelineAPI:
    """Return a madeline API populated with some output"""
    with open(madeline_output, "r") as output:
        madeline_content = output.read()
    madeline_api.process.set_stdout(madeline_content)
    return madeline_api
