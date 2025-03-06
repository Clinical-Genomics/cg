import pytest

from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.config_file import (
    NextflowConfigFileCreator,
)


@pytest.fixture
def raredisease_config_file_content_creator(
    raredisease_context: CGConfig,
) -> NextflowConfigFileCreator:
    return NextflowConfigFileCreator(
        store=raredisease_context.status_db,
        platform=raredisease_context.raredisease.platform,
        workflow_config_path=raredisease_context.raredisease.config,
        resources=raredisease_context.raredisease.resources,
        account=raredisease_context.raredisease.slurm.account,
    )
