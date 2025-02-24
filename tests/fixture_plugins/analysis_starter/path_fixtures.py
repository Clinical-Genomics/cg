import pytest


@pytest.fixture
def dummy_work_dir_path() -> str:
    return "path/to/work/dir"


@pytest.fixture
def dummy_params_file_path() -> str:
    return "path/to/params/file"


@pytest.fixture
def dummy_nextflow_config_path() -> str:
    return "path/to/nextflow/config"
