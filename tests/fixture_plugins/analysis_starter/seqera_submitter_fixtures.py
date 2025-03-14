from pathlib import Path

import pytest

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile, WriteStream
from cg.models.cg_config import SeqeraPlatformConfig
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.services.analysis_starter.submitters.seqera_platform.client import SeqeraPlatformClient
from cg.services.analysis_starter.submitters.seqera_platform.dtos import (
    LaunchRequest,
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
    raredisease_case_config: NextflowCaseConfig, raredisease_params_file_path_readable: Path
) -> WorkflowLaunchRequest:
    parameters: dict = ReadFile.get_content_from_file(
        file_format=FileFormat.YAML, file_path=Path(raredisease_params_file_path_readable)
    )
    parameters_as_string = WriteStream.write_stream_from_content(
        content=parameters, file_format=FileFormat.YAML
    )
    launch = LaunchRequest(
        computeEnvId="normal-id",
        configProfiles=raredisease_case_config.config_profiles,
        configText=f"includeConfig {raredisease_case_config.nextflow_config_file}",
        paramsText=parameters_as_string,
        pipeline=raredisease_case_config.pipeline_repository,
        preRunScript=raredisease_case_config.pre_run_script,
        pullLatest=False,
        resume=False,
        revision=raredisease_case_config.revision,
        runName=raredisease_case_config.case_id,
        sessionId=None,
        stubRun=False,
        workDir=raredisease_case_config.work_dir,
    )
    return WorkflowLaunchRequest(launch=launch)
