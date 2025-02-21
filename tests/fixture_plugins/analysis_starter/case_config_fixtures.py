import pytest

from cg.constants import Workflow
from cg.services.analysis_starter.configurator.models.raredisease import RarediseaseCaseConfig


@pytest.fixture
def raredisease_case_config(
    raredisease_case_id: str,
    dummy_work_dir_path: str,
    dummy_nextflow_config_path: str,
    dummy_params_file_path: str,
) -> RarediseaseCaseConfig:
    return RarediseaseCaseConfig(
        case_id=raredisease_case_id,
        workflow=Workflow.RAREDISEASE,
        case_priority="some_priority",
        netxflow_config_file=dummy_nextflow_config_path,
        params_file=dummy_params_file_path,
        work_dir=dummy_work_dir_path,
    )
