import datetime
from pathlib import Path

import json
import pytest


@pytest.fixture(name="datestamp_now")
def fixture_datestamp_now() -> datetime:
    """Return a now date stamp in datetime format"""
    return datetime.datetime.now()


@pytest.fixture(name="dolores_sample_json_path")
def fixture_dolores_sample_json_path(fixtures_dir) -> Path:
    """Return path to Dolores sample.json path"""
    return Path(fixtures_dir, "store", "dolores", "sample.json")


@pytest.fixture(name="dolores_sample_raw")
def fixture_dolores_sample_raw(dolores_sample_json_path: Path) -> dict:
    """Load an example of json dolores sample"""
    with open(dolores_sample_json_path) as json_file:
        return json.load(json_file)


@pytest.fixture(name="dolores_subject_json_path")
def fixture_dolores_subject_json_path(fixtures_dir) -> Path:
    """Return path to Dolores subject.json path"""
    return Path(fixtures_dir, "store", "dolores", "subject.json")


@pytest.fixture(name="dolores_subject_raw")
def fixture_dolores_subject_raw(dolores_subject_json_path: Path) -> dict:
    """Load an example of json dolores subject"""
    with open(dolores_subject_json_path) as json_file:
        return json.load(json_file)
