from pathlib import Path

from cg.services.analysis_starter.configurator.extensions.abstract import PipelineExtension
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)

GENE_PANEL_FILE_NAME = "gene_panels.bed"
MANAGED_VARIANTS_FILE_NAME = "managed_variants.vcf"

class RarediseaseExtension(PipelineExtension):
    """Contains Raredisease specific file creations which differ from the default Nextflow flow."""

    def __init__(
        self,
        gene_panel_file_creator: GenePanelFileCreator,
        managed_variants_file_creator: ManagedVariantsFileCreator,
    ):
        self.gene_panel_file_creator = gene_panel_file_creator
        self.managed_variants_file_creator = managed_variants_file_creator

    def configure(self, case_id: str, case_run_directory: Path) -> None:
        """Perform pipeline specific actions."""
        self.gene_panel_file_creator.create(case_id=case_id, file_path=self._get_gene_panel_file_path(case_run_directory))
        self.managed_variants_file_creator.create(case_id=case_id, file_path=self._get_managed_variants_file_path(case_run_directory))

    def _get_gene_panel_file_path(self, case_run_directory: Path) -> Path:
        return Path(case_run_directory, GENE_PANEL_FILE_NAME)

    def _get_managed_variants_file_path(self, case_run_directory: Path) -> Path:
        return Path(case_run_directory, MANAGED_VARIANTS_FILE_NAME)
