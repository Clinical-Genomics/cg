from pathlib import Path

from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import GenePanelMasterList
from cg.constants.gene_panel import GenePanelCombo, GenePanelGenomeBuild
from cg.services.analysis_starter.configurator.file_creators.abstract import FileContentCreator
from cg.services.analysis_starter.configurator.file_creators.utils import (
    get_case_id_from_path,
    get_genome_build,
)
from cg.store.models import Case
from cg.store.store import Store


class GenePanelFileContentCreator(FileContentCreator):
    def __init__(self, store: Store, scout_api: ScoutAPI):
        self.store = store
        self.scout_api = scout_api

    def create(self, case_path: Path) -> list[str]:
        case_id: str = get_case_id_from_path(case_path=case_path)
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        genome_build: GenePanelGenomeBuild = get_genome_build(workflow=case.data_analysis)
        all_panels: list[str] = self._get_aggregated_panels(
            customer_id=case.customer.internal_id, default_panels=set(case.panels)
        )
        return self.scout_api.export_panels(build=genome_build, panels=all_panels)

    def _get_aggregated_panels(self, customer_id: str, default_panels: set[str]) -> list[str]:
        """Check if customer is collaborator for gene panel master list
        and if all default panels are included in the gene panel master list.
        If not, add gene panel combo and broad non-specific gene panels.
        Return an aggregated gene panel."""
        if GenePanelMasterList.is_customer_collaborator_and_panels_in_gene_panels_master_list(
            customer_id=customer_id, gene_panels=default_panels
        ):
            return GenePanelMasterList.get_panel_names()
        all_panels: set[str] = self._add_gene_panel_combo(gene_panels=default_panels)
        all_panels |= GenePanelMasterList.get_non_specific_gene_panels()
        return list(all_panels)

    @staticmethod
    def _add_gene_panel_combo(gene_panels: set[str]) -> set[str]:
        """
        Add gene panels combinations for gene panels being part of gene panel combination and
        return updated gene panels.
        """
        additional_panels = set()
        for panel in gene_panels:
            if panel in GenePanelCombo.COMBO_1:
                additional_panels |= GenePanelCombo.COMBO_1.get(panel)
        gene_panels |= additional_panels
        return gene_panels
