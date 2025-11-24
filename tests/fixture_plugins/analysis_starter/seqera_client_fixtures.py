from http import HTTPStatus

import pytest
from requests import Response

from cg.constants.priority import SlurmQos
from cg.io.json import write_json_stream
from cg.models.cg_config import SeqeraPlatformConfig
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.services.analysis_starter.submitters.seqera_platform.client import SeqeraPlatformClient
from cg.services.analysis_starter.submitters.seqera_platform.dtos import (
    LaunchRequest,
    WorkflowLaunchRequest,
)


@pytest.fixture
def seqera_platform_config() -> SeqeraPlatformConfig:
    return SeqeraPlatformConfig(
        base_url="https://base.seqera.url",
        bearer_token="abc123",
        compute_environments={
            SlurmQos.LOW: "low-id",
            SlurmQos.NORMAL: "normal-id",
            SlurmQos.HIGH: "high-id",
            SlurmQos.EXPRESS: "express-id",
        },
        workspace_id=1,
    )


@pytest.fixture
def seqera_platform_client(seqera_platform_config: SeqeraPlatformConfig) -> SeqeraPlatformClient:
    return SeqeraPlatformClient(seqera_platform_config)


@pytest.fixture
def launch_request(raredisease_case_config: NextflowCaseConfig) -> LaunchRequest:
    return LaunchRequest(
        computeEnvId="id",
        configProfiles=raredisease_case_config.config_profiles,
        configText="DummyTextForDummyCase",
        paramsText="DummyTextForDummyCase",
        pipeline=raredisease_case_config.pipeline_repository,
        preRunScript=raredisease_case_config.pre_run_script,
        pullLatest=False,
        revision=raredisease_case_config.revision,
        runName="DummyCase",
        workDir="WorkDirForDummyCase",
    )


@pytest.fixture
def workflow_launch_request(launch_request: LaunchRequest) -> WorkflowLaunchRequest:
    return WorkflowLaunchRequest(launch=launch_request)


@pytest.fixture
def http_workflow_launch_response() -> Response:
    response = Response()
    response.status_code = HTTPStatus.OK.value
    response._content = write_json_stream(
        {"sessionId": "session-id", "workflowId": "DummyId"}  # TODO remove sessionId
    ).encode()
    return response


@pytest.fixture
def http_get_workflow_response() -> Response:
    response = Response()
    response.status_code = HTTPStatus.OK.value
    response._content = write_json_stream(
        {
            "workflow": {
                "id": "some_id",
                "runName": "case_id",
                "sessionId": "some_session_id",
            }
        }
    ).encode()
    return response


@pytest.fixture
def http_not_ok_response() -> Response:
    """Returns a mocked HTTP response with a error status code."""
    response = Response()
    response.status_code = HTTPStatus.IM_A_TEAPOT.value
    response._content = write_json_stream(
        {"error": "Server refuses to brew coffee because it is a teapot."}
    ).encode()
    return response
