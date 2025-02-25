import pytest

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile, WriteStream
from cg.models.cg_config import SeqeraPlatformConfig
from cg.services.analysis_starter.configurator.models.raredisease import RarediseaseCaseConfig
from cg.services.analysis_starter.submitters.seqera_platform.client import SeqeraPlatformClient
from cg.services.analysis_starter.submitters.seqera_platform.dtos import (
    LaunchRequest,
    PipelineResponse,
    WorkflowLaunchRequest,
)
from cg.services.analysis_starter.submitters.seqera_platform.submitter import (
    SeqeraPlatformSubmitter,
)


@pytest.fixture
def seqera_platform_submitter(
    seqera_platform_client: SeqeraPlatformClient, seqera_platform_config: SeqeraPlatformConfig
) -> SeqeraPlatformSubmitter:
    return SeqeraPlatformSubmitter(
        client=seqera_platform_client,
        compute_environment_ids=seqera_platform_config.compute_environments,
    )


@pytest.fixture
def expected_workflow_launch_request(
    pipeline_response: PipelineResponse, raredisease_case_config: RarediseaseCaseConfig
) -> WorkflowLaunchRequest:
    parameters: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML, file_path=raredisease_case_config.params_file
    )
    parameters_as_string = WriteStream.write_stream_from_content(
        content=parameters, file_format=FileFormat.YAML
    )
    launch = LaunchRequest(
        computeEnvId="normal-id",
        configProfiles=pipeline_response.launch.configProfiles,
        configText=f"includeConfig {raredisease_case_config.nextflow_config_file}",
        paramsText=parameters_as_string,
        pipeline=pipeline_response.launch.pipeline,
        preRunScript=pipeline_response.launch.preRunScript,
        pullLatest=pipeline_response.launch.pullLatest,
        resume=False,
        revision=pipeline_response.launch.revision,
        runName=raredisease_case_config.case_id,
        sessionId=None,
        stubRun=False,
        workDir=raredisease_case_config.work_dir.as_posix(),
    )
    return WorkflowLaunchRequest(launch=launch)
