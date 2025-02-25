from cg.services.analysis_starter.configurator.models.raredisease import RarediseaseCaseConfig
from cg.services.analysis_starter.submitters.seqera_platform.dtos import PipelineResponse
from cg.services.analysis_starter.submitters.seqera_platform.submitter import (
    SeqeraPlatformSubmitter,
)


def test_create_launch_request(
    seqera_platform_submitter: SeqeraPlatformSubmitter,
    raredisease_case_config: RarediseaseCaseConfig,
    pipeline_response: PipelineResponse,
):
    # GIVEN a Seqera platform submitter and a case config

    seqera_platform_submitter._create_launch_request(
        case_config=raredisease_case_config, pipeline_config=pipeline_response
    )
