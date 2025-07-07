from pathlib import Path

import pytest

from cg.constants import Workflow
from cg.constants.priority import SlurmQos
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig


@pytest.fixture
def raredisease_repository() -> str:
    return "https://some_url"


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
        stub_run=False,
        work_dir=raredisease_work_dir_path.as_posix(),
    )


@pytest.fixture
def rnafusion_case_config(nextflow_root: str, nextflow_case_id: str) -> NextflowCaseConfig:
    return NextflowCaseConfig(
        case_id=nextflow_case_id,
        workflow=Workflow.RNAFUSION,
        case_priority=SlurmQos.NORMAL,
        config_profiles=["myprofile"],
        nextflow_config_file=Path(
            nextflow_root, nextflow_case_id, f"{nextflow_case_id}_nextflow_config.json"
        ).as_posix(),
        params_file=Path(
            nextflow_root, nextflow_case_id, f"{nextflow_case_id}_params_file.yaml"
        ).as_posix(),
        pipeline_repository="https://some_url",
        pre_run_script="",
        revision="2.2.0",
        stub_run=False,
        work_dir=Path(nextflow_root, nextflow_case_id, "work").as_posix(),
    )
