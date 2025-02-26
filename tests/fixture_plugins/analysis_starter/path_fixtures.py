from pathlib import Path

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


@pytest.fixture
def raredisease_nextflow_config_path(raredisease_dir: Path, raredisease_case_id: str) -> str:
    path = Path(raredisease_dir, raredisease_case_id, f"{raredisease_case_id}_nextflow_config.json")
    return path.as_posix()
