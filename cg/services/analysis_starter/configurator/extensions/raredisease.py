from pathlib import Path

from cg.services.analysis_starter.configurator.extensions.abstract import PipelineExtension
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from cg.services.analysis_starter.configurator.file_creators.managed_variants import (
    ManagedVariantsFileCreator,
)


class RarediseaseExtension(PipelineExtension):
    """Configurator for Raredisease analysis."""

    def __init__(
        self,
        gene_panel_content_creator: GenePanelFileCreator,
        managed_variants_content_creator: ManagedVariantsFileCreator,
    ):
        self.gene_panel_content_creator = gene_panel_content_creator
        self.managed_variants_content_creator = managed_variants_content_creator

    def configure(self, case_path: Path) -> None:
        """Perform pipeline specific actions."""
        self._create_gene_panel(case_path)
        self._create_managed_variants(case_path)

    def _create_gene_panel(self, case_path: Path) -> None:
        raise NotImplementedError

    def _create_managed_variants(self, case_path: Path) -> None:
        raise NotImplementedError
