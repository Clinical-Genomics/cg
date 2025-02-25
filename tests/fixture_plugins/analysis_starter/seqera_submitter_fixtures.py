import pytest

from cg.models.cg_config import SeqeraPlatformConfig
from cg.services.analysis_starter.submitters.seqera_platform.client import SeqeraPlatformClient
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
