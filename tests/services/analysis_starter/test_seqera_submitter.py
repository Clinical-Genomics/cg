from unittest.mock import Mock, call, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.constants.priority import SlurmQos
from cg.exc import SeqeraError
from cg.models.cg_config import SeqeraPlatformConfig
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.services.analysis_starter.submitters.seqera_platform import (
    seqera_platform_submitter as submitter,
)
from cg.services.analysis_starter.submitters.seqera_platform.dtos import (
    LaunchRequest,
    WorkflowLaunchRequest,
)
from cg.services.analysis_starter.submitters.seqera_platform.seqera_platform_client import (
    SeqeraPlatformClient,
)
from cg.services.analysis_starter.submitters.seqera_platform.seqera_platform_submitter import (
    SeqeraPlatformSubmitter,
)


@pytest.fixture
def expected_workflow_launch_request_with_resume() -> WorkflowLaunchRequest:
    return WorkflowLaunchRequest(
        launch=LaunchRequest(
            id="previous_launch_id",
            computeEnvId="normal-id",
            configProfiles=["profile"],
            configText="includeConfig 'path_to_config.config'",
            paramsText="content: some-params-content\n",
            pipeline="some.repository",
            preRunScript="pre-run-script",
            pullLatest=False,
            resume=True,
            revision="3.0.0",
            runName="case_id_resumed_2025-11-20_13-37",
            sessionId="some_session_id",
            workDir="work/dir",
        )
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


@pytest.mark.freeze_time("2025-11-20 13:37")
def test_submit_with_resume(
    expected_workflow_launch_request_with_resume: WorkflowLaunchRequest,
    seqera_platform_config: SeqeraPlatformConfig,
    mocker: MockerFixture,
):
    # GIVEN a case config containing a session id and resume set to True
    case_config = NextflowCaseConfig(
        case_id="case_id",
        case_priority=SlurmQos.NORMAL,
        config_profiles=["profile"],
        nextflow_config_file="path_to_config.config",
        params_file="params_file.yaml",
        pipeline_repository="some.repository",
        pre_run_script="pre-run-script",
        resume=True,
        workflow_id="previous_workflow_id",
        revision="3.0.0",
        session_id="some_session_id",
        work_dir="work/dir",
        workflow=Workflow.RAREDISEASE,
    )

    # GIVEN a SeqeraPlatformSubmitter
    client = create_autospec(SeqeraPlatformClient)
    client.launch_workflow = Mock(return_value={"workflowId": "some_workflow_id"})
    client.get_workflow = Mock(
        side_effect=[
            {"workflow": {"sessionId": "some_session_id", "launchId": "previous_launch_id"}},
            {
                "workflow": {
                    "id": "some_id",
                    "runName": "case_id",
                    "sessionId": "some_session_id",
                }
            },
        ]
    )
    seqera_platform_submitter = SeqeraPlatformSubmitter(
        client=client, compute_environment_ids=seqera_platform_config.compute_environments
    )

    mocker.patch.object(submitter, "read_yaml", return_value={"content": "some-params-content"})

    # WHEN calling submit
    submit_result: CaseConfig = seqera_platform_submitter.submit(case_config)

    # THEN the session id and the workflow id should be as expected
    assert submit_result.get_session_id() == "some_session_id"
    assert submit_result.get_workflow_id() == "some_workflow_id"

    # THEN assert that the run request provided to the client is correct
    client.launch_workflow.assert_called_once_with(expected_workflow_launch_request_with_resume)
    assert client.get_workflow.call_args_list == [
        call("previous_workflow_id"),
        call("some_workflow_id"),
    ]
    assert case_config.workflow_id == "previous_workflow_id"


def test_submit_no_workflow_id(seqera_platform_config: SeqeraPlatformConfig, mocker: MockerFixture):
    # GIVEN a case config
    case_config = NextflowCaseConfig(
        case_id="case_id",
        case_priority=SlurmQos.NORMAL,
        config_profiles=["profile"],
        nextflow_config_file="path_to_config.config",
        params_file="params_file.yaml",
        pipeline_repository="some.repository",
        pre_run_script="pre-run-script",
        resume=False,
        revision="3.0.0",
        session_id=None,
        work_dir="work/dir",
        workflow=Workflow.RAREDISEASE,
    )

    # GIVEN that Seqera platform does not respond with a workflowId
    client = create_autospec(SeqeraPlatformClient)
    client.launch_workflow = Mock(return_value={"cat": "dog"})
    seqera_platform_submitter = SeqeraPlatformSubmitter(
        client=client, compute_environment_ids=seqera_platform_config.compute_environments
    )

    # GIVEN that yamls can be read
    mocker.patch.object(submitter, "read_yaml", return_value={})

    # WHEN calling submit
    # THEN a SeqeraError is raised
    with pytest.raises(SeqeraError):
        seqera_platform_submitter.submit(case_config)


def test_submit_no_session_id(seqera_platform_config: SeqeraPlatformConfig, mocker: MockerFixture):
    # GIVEN a case config
    case_config = NextflowCaseConfig(
        case_id="case_id",
        case_priority=SlurmQos.NORMAL,
        config_profiles=["profile"],
        nextflow_config_file="path_to_config.config",
        params_file="params_file.yaml",
        pipeline_repository="some.repository",
        pre_run_script="pre-run-script",
        resume=False,
        revision="3.0.0",
        session_id=None,
        work_dir="work/dir",
        workflow=Workflow.RAREDISEASE,
    )

    # GIVEN that Seqera platform responds with a workflowId but no sessionId
    client = create_autospec(SeqeraPlatformClient)
    client.launch_workflow = Mock(return_value={"workflowId": "some_workflow_id"})
    client.get_workflow = Mock(return_value={"cat": "dog"})
    seqera_platform_submitter = SeqeraPlatformSubmitter(
        client=client, compute_environment_ids=seqera_platform_config.compute_environments
    )

    # GIVEN that yamls can be read
    mocker.patch.object(submitter, "read_yaml", return_value={})

    # WHEN calling submit
    # THEN a SeqeraError is raised
    with pytest.raises(SeqeraError):
        seqera_platform_submitter.submit(case_config)


@pytest.mark.parametrize(
    "workflow_id, session_id, workflow_response, error",
    [
        (None, "session_id", {}, "workflow ID and session ID"),
        ("previous_workflow_id", None, {}, "workflow ID and session ID"),
        ("previous_workflow_id", "session_id", {}, "session does not match"),
        (
            "previous_workflow_id",
            "session_id",
            {"sessionId": "other_session", "launchId": "launch_id"},
            "session does not match",
        ),
        ("previous_workflow_id", "session_id", {"sessionId": "session_id"}, "No launchId"),
    ],
)
def test_submit_resume_invalid_previous_workflow(
    workflow_id: str | None,
    session_id: str | None,
    workflow_response: dict,
    error: str,
    raredisease_case_config: NextflowCaseConfig,
    seqera_platform_config: SeqeraPlatformConfig,
    mocker: MockerFixture,
):
    # GIVEN a resume request with missing or mismatched previous workflow metadata
    raredisease_case_config.resume = True
    raredisease_case_config.workflow_id = workflow_id
    raredisease_case_config.session_id = session_id
    client = create_autospec(SeqeraPlatformClient)
    client.get_workflow.return_value = {"workflow": workflow_response}
    platform_submitter = SeqeraPlatformSubmitter(
        client=client, compute_environment_ids=seqera_platform_config.compute_environments
    )
    mocker.patch.object(submitter, "read_yaml", return_value={})

    # WHEN submitting, THEN no workflow is launched and an actionable error is raised
    with pytest.raises(SeqeraError, match=error):
        platform_submitter.submit(raredisease_case_config)
    client.launch_workflow.assert_not_called()


def test_submit_fresh_launch(
    raredisease_case_config: NextflowCaseConfig,
    seqera_platform_config: SeqeraPlatformConfig,
    mocker: MockerFixture,
):
    # GIVEN a fresh launch and a client returning the new workflow and session
    client = create_autospec(SeqeraPlatformClient)
    client.launch_workflow.return_value = {"workflowId": "new_workflow_id"}
    client.get_workflow.return_value = {"workflow": {"sessionId": "new_session_id"}}
    platform_submitter = SeqeraPlatformSubmitter(
        client=client, compute_environment_ids=seqera_platform_config.compute_environments
    )
    mocker.patch.object(submitter, "read_yaml", return_value={})

    # WHEN submitting the case
    result = platform_submitter.submit(raredisease_case_config)

    # THEN no previous workflow is looked up and no launch ID is supplied
    client.get_workflow.assert_called_once_with("new_workflow_id")
    request = client.launch_workflow.call_args.args[0]
    assert request.launch.id is None
    assert request.launch.resume is False
    assert result.workflow_id == "new_workflow_id"
    assert result.session_id == "new_session_id"
