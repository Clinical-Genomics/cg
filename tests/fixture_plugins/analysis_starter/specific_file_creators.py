import pytest

from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.configurator.file_creators.nextflow.gene_panel import (
    GenePanelFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.managed_variants import (
    ManagedVariantsFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_mapping import (
    SampleMappingFileCreator,
)


@pytest.fixture
def raredisease_gene_panel_creator(
    raredisease_context: CGConfig,
) -> GenePanelFileCreator:
    return GenePanelFileCreator(
        store=raredisease_context.status_db,
        scout_api=raredisease_context.scout_api_37,
    )


@pytest.fixture
def raredisease_managed_variants_creator(
    raredisease_context: CGConfig,
) -> ManagedVariantsFileCreator:
    return ManagedVariantsFileCreator(
        store=raredisease_context.status_db,
        scout_api=raredisease_context.scout_api_37,
    )


@pytest.fixture
def raredisease_sample_mapping_file_creator(
    raredisease_context: CGConfig,
) -> SampleMappingFileCreator:
    """Fixture for the raredisease sample mapping file creator."""
    return SampleMappingFileCreator(store=raredisease_context.status_db)
