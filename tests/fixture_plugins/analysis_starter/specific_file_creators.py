import pytest

from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)


@pytest.fixture
def raredisease_gene_panel_creator(
    raredisease_context: CGConfig,
) -> GenePanelFileCreator:
    return GenePanelFileCreator(
        store=raredisease_context.status_db,
        scout_api=raredisease_context.scout_api,
    )


@pytest.fixture
def raredisease_managed_variants_creator(
    raredisease_context: CGConfig,
) -> ManagedVariantsFileCreator:
    return ManagedVariantsFileCreator(
        store=raredisease_context.status_db,
        scout_api=raredisease_context.scout_api,
    )
