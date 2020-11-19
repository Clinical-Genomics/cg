"""Fixtures for the scout api tests"""

from pathlib import Path

import pytest

from cg.apps.scoutapi import ScoutAPI
from tests.mocks.process_mock import ProcessMock


class MockScoutApi(ScoutAPI):
    def __init__(self, config: dict):
        binary_path = "scout"
        config_path = "config_path"
        self.process = ProcessMock(binary=binary_path, config=config_path)


@pytest.fixture(name="scout_dir")
def fixture_scout_dir(apps_dir: Path) -> Path:
    """Return the path to the scout fixtures dir"""
    return apps_dir / "scout"


@pytest.fixture(name="causatives_file")
def fixture_causatives_file(scout_dir: Path) -> Path:
    """Return the path to a file with causatives output"""
    return scout_dir / "export_causatives.json"


@pytest.fixture(name="causative_output")
def fixture_causative_output(causatives_file: Path) -> str:
    """Return the content of a export causatives run with scout"""
    with open(causatives_file, "r") as infile:
        content = infile.read()
    return content


@pytest.fixture(name="scout_api")
def fixture_scout_api() -> ScoutAPI:
    return MockScoutApi({})
