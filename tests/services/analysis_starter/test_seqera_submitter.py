from pytest_mock import MockerFixture

from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.services.analysis_starter.submitters.seqera_platform import (
    seqera_platform_submitter as submitter,
)
from cg.services.analysis_starter.submitters.seqera_platform.dtos import WorkflowLaunchRequest
from cg.services.analysis_starter.submitters.seqera_platform.seqera_platform_submitter import (
    SeqeraPlatformSubmitter,
)


def test_create_launch_request(
    seqera_platform_submitter: SeqeraPlatformSubmitter,
    raredisease_case_config: NextflowCaseConfig,
    expected_raredisease_workflow_params_content: dict,
    expected_workflow_launch_request: WorkflowLaunchRequest,
    mocker: MockerFixture,
):
    # GIVEN a Seqera platform submitter and a case config

    # GIVEN that the read_yaml method returns the expected parameters content
    mocker.patch.object(
        submitter, "read_yaml", return_value=expected_raredisease_workflow_params_content
    )

    # WHEN creating a workflow launch request
    workflow_launch_request: WorkflowLaunchRequest = (
        seqera_platform_submitter._create_launch_request(case_config=raredisease_case_config)
    )

    # THEN the workflow launch request should be populated
    assert workflow_launch_request == expected_workflow_launch_request
