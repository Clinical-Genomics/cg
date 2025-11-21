from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.constants import Workflow
from cg.constants.priority import SlurmQos
from cg.models.cg_config import SeqeraPlatformConfig
from cg.services.analysis_starter.configurator.abstract_model import CaseConfig
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.services.analysis_starter.submitters.seqera_platform import (
    seqera_platform_submitter as submitter,
)
from cg.services.analysis_starter.submitters.seqera_platform.client import SeqeraPlatformClient
from cg.services.analysis_starter.submitters.seqera_platform.dtos import (
    LaunchRequest,
    WorkflowLaunchRequest,
)
from cg.services.analysis_starter.submitters.seqera_platform.seqera_platform_submitter import (
    SeqeraPlatformSubmitter,
)


@pytest.fixture
def expected_workflow_launch_request_with_resume() -> WorkflowLaunchRequest:
    return WorkflowLaunchRequest(
        launch=LaunchRequest(
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
        revision="3.0.0",
        session_id="some_session_id",
        work_dir="work/dir",
        workflow=Workflow.RAREDISEASE,
    )

    # GIVEN a SeqeraPlatformSubmitter
    client = create_autospec(SeqeraPlatformClient)
    client.run_case = Mock(
        return_value={"workflowId": "some_workflow_id", "sessionId": "some_session_id"}
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
    client.run_case.assert_called_once_with(expected_workflow_launch_request_with_resume)
