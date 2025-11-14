from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.constants.priority import SlurmQos
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


def test_submit_with_resume(seqera_platform_submitter: SeqeraPlatformSubmitter):
    # GIVEN a case config containing a session id and resume set to True
    case_config = NextflowCaseConfig(
        case_id="case_id",
        case_priority=SlurmQos.NORMAL,
        config_profiles=["profile"],
        nextflow_config_file="path_to_config.config",
        params_file="params_file.yaml",
        pipeline_repository="some.repository",
        pre_run_script="pre-run-script",
        revision="3.0.0",
        work_dir="work/dir",
        workflow=Workflow.RAREDISEASE,
    )

    # WHEN calling submit
    session_id, workflow_id = seqera_platform_submitter.submit(case_config)

    # THEN the session id and the workflow id should be as expected
    assert session_id == "some_session_id"
    assert workflow_id == "some_workflow_id"

    # THEN assert that the run request provided to the client is correct
