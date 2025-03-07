import pytest

from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator


@pytest.fixture
def raredisease_gene_panel_content_creator(
    raredisease_context: CGConfig,
) -> GenePanelFileCreator:
    return GenePanelFileCreator(
        store=raredisease_context.status_db,
        scout_api=raredisease_context.scout_api,
    )
