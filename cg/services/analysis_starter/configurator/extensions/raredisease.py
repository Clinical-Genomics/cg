from pathlib import Path

from cg.constants.nf_analysis import NextflowFileType
from cg.services.analysis_starter.configurator.extensions.abstract import PipelineExtension
from cg.services.analysis_starter.configurator.file_creators.gene_panel import (
    GenePanelFileContentCreator,
)
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileContentCreator,
)
from cg.services.analysis_starter.configurator.file_creators.utils import create_file


class RarediseaseExtension(PipelineExtension):
    """Configurator for Raredisease analysis."""

    def __init__(
        self,
        gene_panel_content_creator: GenePanelFileContentCreator,
        managed_variants_content_creator: ManagedVariantsFileContentCreator,
    ):
        self.gene_panel_content_creator = gene_panel_content_creator
        self.managed_variants_content_creator = managed_variants_content_creator

    def configure(self, case_path: Path) -> None:
        """Perform pipeline specific actions."""
        self._create_gene_panel(case_path)
        self._create_managed_variants(case_path)

    def _create_gene_panel(self, case_path: Path) -> None:
        create_file(
            content_creator=self.gene_panel_content_creator,
            case_path=case_path,
            file_type=NextflowFileType.GENE_PANEL,
        )

    def _create_managed_variants(self, case_path: Path) -> None:
        create_file(
            content_creator=self.managed_variants_content_creator,
            case_path=case_path,
            file_type=NextflowFileType.MANAGED_VARIANTS,
        )
