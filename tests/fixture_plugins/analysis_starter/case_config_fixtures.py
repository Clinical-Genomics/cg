from pathlib import Path

import pytest

from cg.constants import Workflow
from cg.constants.priority import SlurmQos
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig


@pytest.fixture
def raredisease_case_config(
    raredisease_case_id: str,
    raredisease_work_dir_path: Path,
    raredisease_nextflow_config_file_path: Path,
    raredisease_params_file_path: Path,
) -> NextflowCaseConfig:
    return NextflowCaseConfig(
        case_id=raredisease_case_id,
        workflow=Workflow.RAREDISEASE,
        case_priority=SlurmQos.NORMAL,
        nextflow_config_file=raredisease_nextflow_config_file_path.as_posix(),
        params_file=raredisease_params_file_path.as_posix(),
        work_dir=raredisease_work_dir_path.as_posix(),
    )
