import pytest

from cg.io.yaml import write_yaml_stream
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
    raredisease_case_config: NextflowCaseConfig, expected_raredisease_workflow_params_content: dict
) -> WorkflowLaunchRequest:
    parameter_stream: str = write_yaml_stream(expected_raredisease_workflow_params_content)
    launch = LaunchRequest(
        computeEnvId="normal-id",
        configProfiles=raredisease_case_config.config_profiles,
        configText=f"includeConfig '{raredisease_case_config.nextflow_config_file}'",
        paramsText=parameter_stream,
        pipeline=raredisease_case_config.pipeline_repository,
        preRunScript=raredisease_case_config.pre_run_script,
        pullLatest=False,
        resume=False,
        revision=raredisease_case_config.revision,
        runName=raredisease_case_config.case_id,
        sessionId=None,
        workDir=raredisease_case_config.work_dir,
    )
    return WorkflowLaunchRequest(launch=launch)
