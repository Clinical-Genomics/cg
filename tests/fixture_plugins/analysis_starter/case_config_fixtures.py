from pathlib import Path

import pytest

from cg.constants import Workflow
from cg.constants.priority import SlurmQos
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig


@pytest.fixture
def raredisease_repository() -> str:
    return "http://some_url"


@pytest.fixture
def raredisease_revision() -> str:
    return "2.2.0"


@pytest.fixture
def raredisease_config_profiles() -> list[str]:
    return ["myprofile"]


@pytest.fixture
def raredisease_case_config(
    raredisease_case_id: str,
    raredisease_config_profiles: list[str],
    raredisease_nextflow_config_file_path: Path,
    raredisease_params_file_path: Path,
    raredisease_repository: str,
    raredisease_revision: str,
    raredisease_work_dir_path: Path,
) -> NextflowCaseConfig:

    return NextflowCaseConfig(
        case_id=raredisease_case_id,
        config_profiles=raredisease_config_profiles,
        workflow=Workflow.RAREDISEASE,
        case_priority=SlurmQos.NORMAL,
        nextflow_config_file=raredisease_nextflow_config_file_path.as_posix(),
        params_file=raredisease_params_file_path.as_posix(),
        pipeline_repository=raredisease_repository,
        pre_run_script="",
        revision=raredisease_revision,
        work_dir=raredisease_work_dir_path.as_posix(),
    )
