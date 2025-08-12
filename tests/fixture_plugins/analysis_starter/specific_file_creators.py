from unittest.mock import create_autospec

import pytest

from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.nextflow.managed_variants import (
    ManagedVariantsFileCreator,
)


@pytest.fixture
def raredisease_managed_variants_creator(
    raredisease_context: CGConfig,
) -> ManagedVariantsFileCreator:
    return ManagedVariantsFileCreator(
        store=raredisease_context.status_db,
        scout_api=raredisease_context.scout_api_37,
    )
