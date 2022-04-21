from pathlib import Path

import json
import pytest


@pytest.fixture(name="dolores_subject_json_path")
def fixture_dolores_subject_json_path(fixtures_dir) -> Path:
    """Return path to Dolores subject.json path"""
    return Path(fixtures_dir, "store", "dolores", "subject", "subject.json")


@pytest.fixture(name="dolores_subject_raw")
def fixture_dolores_subject_raw(dolores_subject_json_path: Path) -> dict:
    """Load an example of json dolores subject"""
    with open(dolores_subject_json_path) as json_file:
        return json.load(json_file)
