import pytest

from cg.services.analysis_starter.configurator.extensions.raredisease import RarediseaseExtension
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)


@pytest.fixture
def raredisease_extension(
    raredisease_gene_panel_creator: GenePanelFileCreator,
    raredisease_managed_variants_creator: ManagedVariantsFileCreator,
) -> RarediseaseExtension:
    return RarediseaseExtension(
        gene_panel_file_creator=raredisease_gene_panel_creator,
        managed_variants_file_creator=raredisease_managed_variants_creator,
    )
