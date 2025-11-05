import pytest

from cg.apps.lims import LimsAPI
from cg.services.analysis_starter.configurator.file_creators.microsalt_config import (
    MicrosaltConfigFileCreator,
)
from cg.store.store import Store


@pytest.fixture
def microsalt_config_file_creator(
    microsalt_store: Store, lims_api: LimsAPI
) -> MicrosaltConfigFileCreator:
    return MicrosaltConfigFileCreator(
        lims_api=lims_api, queries_path="/dev/null", store=microsalt_store
    )
