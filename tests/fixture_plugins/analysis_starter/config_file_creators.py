import pytest

from cg.apps.lims import LimsAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.microsalt_config import (
    MicrosaltConfigFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.config_file import (
    NextflowConfigFileCreator,
)
from cg.store.store import Store


@pytest.fixture
def microsalt_config_file_creator(
    microsalt_store: Store, lims_api: LimsAPI
) -> MicrosaltConfigFileCreator:
    return MicrosaltConfigFileCreator(
        lims_api=lims_api, queries_path="/dev/null", store=microsalt_store
    )


@pytest.fixture
def raredisease_config_file_creator(
    raredisease_context: CGConfig,
) -> NextflowConfigFileCreator:
    return NextflowConfigFileCreator(
        store=raredisease_context.status_db,
        platform=raredisease_context.raredisease.platform,
        workflow_config_path=raredisease_context.raredisease.config,
        resources=raredisease_context.raredisease.resources,
        account=raredisease_context.raredisease.slurm.account,
    )
