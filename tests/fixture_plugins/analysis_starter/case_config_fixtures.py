import pytest

from cg.constants import Priority, Workflow
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig


@pytest.fixture
def raredisease_case_config(
    raredisease_case_id: str,
    dummy_work_dir_path: str,
    dummy_nextflow_config_path: str,
    dummy_params_file_path: str,
) -> NextflowCaseConfig:
    return NextflowCaseConfig(
        case_id=raredisease_case_id,
        workflow=Workflow.RAREDISEASE,
        case_priority=Priority.standard,
        netxflow_config_file=dummy_nextflow_config_path,
        params_file=dummy_params_file_path,
        work_dir=dummy_work_dir_path,
    )
