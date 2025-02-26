from pathlib import Path

import pytest


@pytest.fixture
def dummy_work_dir_path() -> str:
    return "path/to/work/dir"


@pytest.fixture
def dummy_params_file_path(fixtures_dir) -> str:
    return Path(fixtures_dir, "services", "analysis_starter", "case_params_file.yaml").as_posix()


@pytest.fixture
def dummy_nextflow_config_path(fixtures_dir) -> str:
    return Path(
        fixtures_dir, "services", "analysis_starter", "case_nextflow_config.json"
    ).as_posix()
