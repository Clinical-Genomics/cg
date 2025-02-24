from http import HTTPStatus

import pytest
from requests import Response

from cg.constants import Workflow
from cg.constants.constants import FileFormat
from cg.constants.priority import SlurmQos
from cg.io.controller import WriteStream
from cg.models.cg_config import SeqeraPlatformConfig
from cg.services.analysis_starter.submitters.seqera_platform.client import SeqeraPlatformClient
from cg.services.analysis_starter.submitters.seqera_platform.dtos import (
    LaunchResponse,
    PipelineResponse,
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
        workflow_ids={Workflow.RAREDISEASE: 1},
        workspace_id=1,
    )


@pytest.fixture
def seqera_platform_client(seqera_platform_config: SeqeraPlatformConfig) -> SeqeraPlatformClient:
    return SeqeraPlatformClient(seqera_platform_config)


@pytest.fixture
def launch_response() -> LaunchResponse:
    return LaunchResponse(
        configProfiles=["singularity"],
        pipeline="https://some.github.repo",
        preRunScript="",
        pullLatest=False,
        revision="1.0.0",
    )


@pytest.fixture
def pipeline_response(launch_response: LaunchResponse) -> PipelineResponse:
    return PipelineResponse(launch=launch_response)


@pytest.fixture
def http_pipeline_response(pipeline_response: PipelineResponse) -> Response:
    response = Response()
    response.status_code = HTTPStatus.OK.value
    response._content = WriteStream.write_stream_from_content(
        file_format=FileFormat.JSON,
        content=pipeline_response.model_dump(),
    ).encode()
    return response
