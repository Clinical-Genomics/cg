import datetime
from pathlib import Path

import json
import pytest


def get_dict_from_json(file_path: Path) -> dict:
    """Get dict from json file"""
    with open(file_path) as json_file:
        return json.load(json_file)


@pytest.fixture(name="datestamp_now")
def fixture_datestamp_now() -> datetime:
    """Return a now date stamp in datetime format"""
    return datetime.datetime.now()


@pytest.fixture(name="loqusdb_id")
def fixture_loqusdb_id() -> str:
    """Return a loqusdb_id"""
    return "a_loqusdb_id"


@pytest.fixture(name="dolores_application_json_path")
def fixture_dolores_application_json_path(fixtures_dir) -> Path:
    """Return path to Dolores application.json path"""
    return Path(fixtures_dir, "store", "dolores", "application.json")


@pytest.fixture(name="dolores_application_raw")
def fixture_dolores_application_raw(dolores_application_json_path: Path) -> dict:
    """Load an example of json dolores application"""
    return get_dict_from_json(file_path=dolores_application_json_path)


@pytest.fixture(name="dolores_case_json_path")
def fixture_dolores_case_json_path(fixtures_dir) -> Path:
    """Return path to Dolores case.json path"""
    return Path(fixtures_dir, "store", "dolores", "case.json")


@pytest.fixture(name="dolores_case_raw")
def fixture_dolores_case_raw(dolores_case_json_path: Path) -> dict:
    """Load an example of json dolores case"""
    return get_dict_from_json(file_path=dolores_case_json_path)


@pytest.fixture(name="dolores_case_relation_json_path")
def fixture_dolores_case_relation_json_path(fixtures_dir) -> Path:
    """Return path to Dolores case_relation.json path"""
    return Path(fixtures_dir, "store", "dolores", "case_relation.json")


@pytest.fixture(name="dolores_case_relation_raw")
def fixture_dolores_case_relation_raw(dolores_case_relation_json_path: Path) -> dict:
    """Load an example of json dolores case_relation"""
    return get_dict_from_json(file_path=dolores_case_relation_json_path)


@pytest.fixture(name="dolores_experiment_design_json_path")
def fixture_dolores_experiment_design_json_path(fixtures_dir) -> Path:
    """Return path to Dolores experiment_design.json path"""
    return Path(fixtures_dir, "store", "dolores", "experiment_design.json")


@pytest.fixture(name="dolores_experiment_design_raw")
def fixture_dolores_experiment_design_raw(dolores_experiment_design_json_path: Path) -> dict:
    """Load an example of json dolores experiment_design"""
    return get_dict_from_json(file_path=dolores_experiment_design_json_path)


@pytest.fixture(name="dolores_sample_json_path")
def fixture_dolores_sample_json_path(fixtures_dir) -> Path:
    """Return path to Dolores sample.json path"""
    return Path(fixtures_dir, "store", "dolores", "sample.json")


@pytest.fixture(name="dolores_sample_raw")
def fixture_dolores_sample_raw(dolores_sample_json_path: Path) -> dict:
    """Load an example of json dolores sample"""
    return get_dict_from_json(file_path=dolores_sample_json_path)


@pytest.fixture(name="dolores_sequencing_json_path")
def fixture_dolores_sequencing_json_path(fixtures_dir) -> Path:
    """Return path to Dolores sequencing.json path"""
    return Path(fixtures_dir, "store", "dolores", "sequencing.json")


@pytest.fixture(name="dolores_sequencing_raw")
def fixture_dolores_sequencing_raw(dolores_sequencing_json_path: Path) -> dict:
    """Load an example of json dolores sequencing"""
    return get_dict_from_json(file_path=dolores_sequencing_json_path)


@pytest.fixture(name="dolores_subject_json_path")
def fixture_dolores_subject_json_path(fixtures_dir) -> Path:
    """Return path to Dolores subject.json path"""
    return Path(fixtures_dir, "store", "dolores", "subject.json")


@pytest.fixture(name="dolores_subject_raw")
def fixture_dolores_subject_raw(dolores_subject_json_path: Path) -> dict:
    """Load an example of json dolores subject"""
    return get_dict_from_json(file_path=dolores_subject_json_path)
