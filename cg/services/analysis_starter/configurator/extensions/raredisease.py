from pathlib import Path

from cg.services.analysis_starter.configurator.extensions.abstract import PipelineExtension
from cg.services.analysis_starter.configurator.file_creators.nextflow.gene_panel import (
    GenePanelFileCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.managed_variants import (
    ManagedVariantsFileCreator,
)


class RarediseaseExtension(PipelineExtension):
    """Contains Raredisease specific file creations which differ from the default Nextflow flow."""

    def __init__(
        self,
        gene_panel_file_creator: GenePanelFileCreator,
        managed_variants_file_creator: ManagedVariantsFileCreator,
    ):
        self.gene_panel_file_creator = gene_panel_file_creator
        self.managed_variants_file_creator = managed_variants_file_creator

    def configure(self, case_id: str, case_path: Path) -> None:
        """Perform pipeline specific actions."""
        self.gene_panel_file_creator.create(case_id=case_id, case_path=case_path)
        self.managed_variants_file_creator.create(case_id=case_id, case_path=case_path)
