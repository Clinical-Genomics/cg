import pytest

from cg.services.analysis_starter.configurator.extensions.raredisease import RarediseaseExtension
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
def raredisease_extension(
    raredisease_gene_panel_creator: GenePanelFileCreator,
    raredisease_managed_variants_creator: ManagedVariantsFileCreator,
    raredisease_sample_mapping_file_creator: SampleMappingFileCreator,
) -> RarediseaseExtension:
    return RarediseaseExtension(
        gene_panel_file_creator=raredisease_gene_panel_creator,
        managed_variants_file_creator=raredisease_managed_variants_creator,
        sample_mapping_file_creator=raredisease_sample_mapping_file_creator,
    )
