import shutil
from pathlib import Path

from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.services.analysis_starter.submitters.seqera_platform.dtos import WorkflowLaunchRequest
from cg.services.analysis_starter.submitters.seqera_platform.submitter import (
    SeqeraPlatformSubmitter,
)


def test_create_launch_request(
    seqera_platform_submitter: SeqeraPlatformSubmitter,
    raredisease_case_config: NextflowCaseConfig,
    raredisease_params_file_path_readable: Path,
    expected_workflow_launch_request: WorkflowLaunchRequest,
):
    # GIVEN a Seqera platform submitter and a case config

    # GIVEN that the params file exists
    Path(raredisease_case_config.params_file).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(raredisease_params_file_path_readable, raredisease_case_config.params_file)

    # WHEN creating a workflow launch request
    workflow_launch_request: WorkflowLaunchRequest = (
        seqera_platform_submitter._create_launch_request(case_config=raredisease_case_config)
    )

    # THEN the workflow launch request should be populated
    assert workflow_launch_request == expected_workflow_launch_request
