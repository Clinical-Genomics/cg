from pathlib import Path

from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import FileExtensions, GenePanelMasterList
from cg.constants.gene_panel import GenePanelCombo, GenePanelGenomeBuild
from cg.io.txt import write_txt
from cg.services.analysis_starter.configurator.file_creators.nextflow.utils import get_genome_build
from cg.store.models import Case
from cg.store.store import Store


class GenePanelFileCreator:
    def __init__(self, store: Store, scout_api: ScoutAPI):
        self.store = store
        self.scout_api = scout_api

    @staticmethod
    def get_file_path(case_path: Path) -> Path:
        return Path(case_path, "gene_panels").with_suffix(FileExtensions.BED)

    def create(self, case_id: str, case_path: Path) -> None:
        file_path: Path = self.get_file_path(case_path)
        content: list[str] = self._get_content(case_id)
        write_txt(file_path=file_path, content=content)

    def _get_content(self, case_id: str) -> list[str]:
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        genome_build: GenePanelGenomeBuild = get_genome_build(workflow=case.data_analysis)
        all_panels: list[str] = self._get_aggregated_panels(
            customer_id=case.customer.internal_id, default_panels=set(case.panels)
        )
        return self.scout_api.export_panels(build=genome_build, panels=all_panels)

    def _get_aggregated_panels(self, customer_id: str, default_panels: set[str]) -> list[str]:
        """Check if the customer is collaborator for gene panel master list
        and if all default panels are included in the gene panel master list.
        If not, add gene panel combo and broad non-specific gene panels.
        Return an aggregated gene panel."""
        if GenePanelMasterList.is_customer_collaborator_and_panels_in_gene_panels_master_list(
            customer_id=customer_id, gene_panels=default_panels
        ):
            return GenePanelMasterList.get_panel_names()
        all_panels: set[str] = self._add_gene_panels_in_combo(gene_panels=default_panels)
        all_panels |= GenePanelMasterList.get_non_specific_gene_panels()
        return list(all_panels)

    @staticmethod
    def _add_gene_panels_in_combo(gene_panels: set[str]) -> set[str]:
        """
        Return an expanded list of gene panels with all gene panels that belong to the same combo.

        Some panels require the presence of other panels. These panels are said to belong to the
        same combo. This method expands the given panel set, adding all necessary panels
        (panels in the same combo) for each panel in the given set.
        """
        additional_panels = set()
        for panel in gene_panels:
            if panel in GenePanelCombo.COMBO_1:
                additional_panels |= GenePanelCombo.COMBO_1.get(panel)
        gene_panels |= additional_panels
        return gene_panels
