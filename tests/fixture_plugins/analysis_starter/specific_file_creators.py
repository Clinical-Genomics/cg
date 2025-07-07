from unittest.mock import create_autospec

import pytest

from cg.apps.scout.scoutapi import ScoutAPI
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.nextflow.gene_panel import (
    GenePanelFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.managed_variants import (
    ManagedVariantsFileCreator,
)
from cg.store.models import Case
from cg.store.store import Store


@pytest.fixture
def raredisease_gene_panel_creator(raredisease_context: CGConfig) -> GenePanelFileCreator:
    return GenePanelFileCreator(
        store=raredisease_context.status_db,
        scout_api=raredisease_context.scout_api_37,
    )


@pytest.fixture
def nextflow_gene_panel_creator() -> GenePanelFileCreator:
    mock_store: Store = create_autospec(Store)
    mock_store.get_case_by_internal_id.return_value = create_autospec(Case)
    return GenePanelFileCreator(
        store=mock_store,
        scout_api=create_autospec(ScoutAPI),
    )


@pytest.fixture
def raredisease_managed_variants_creator(
    raredisease_context: CGConfig,
) -> ManagedVariantsFileCreator:
    return ManagedVariantsFileCreator(
        store=raredisease_context.status_db,
        scout_api=raredisease_context.scout_api_37,
    )
