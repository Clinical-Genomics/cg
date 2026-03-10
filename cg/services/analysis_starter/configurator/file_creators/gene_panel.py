import logging
from pathlib import Path

from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants import GenePanelMasterList
from cg.constants.gene_panel import GenePanelGenomeBuild
from cg.io.txt import write_txt_with_newlines
from cg.services.analysis_starter.configurator.file_creators.nextflow.utils import get_genome_build
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class GenePanelFileCreator:
    def __init__(self, store: Store, scout_api: ScoutAPI):
        self.store = store
        self.scout_api = scout_api

    def create(self, case_id: str, file_path: Path, double_hashtag_filtering: bool = False) -> None:
        content: list[str] = self._get_content(
            case_id=case_id, double_hashtag_filtering=double_hashtag_filtering
        )
        write_txt_with_newlines(file_path=file_path, content=content)
        LOG.info(f"Created gene panel file for case {case_id} at {file_path}")

    def _get_content(self, case_id: str, double_hashtag_filtering: bool) -> list[str]:
        case: Case = self.store.get_case_by_internal_id_strict(internal_id=case_id)
        genome_build: GenePanelGenomeBuild = get_genome_build(workflow=case.data_analysis)
        all_panels: list[str] = self._get_aggregated_panels(
            customer_id=case.customer.internal_id, default_panels=set(case.panels)
        )
        panels: list[str] = self.scout_api.export_panels(build=genome_build, panels=all_panels)
        if double_hashtag_filtering:
            panels = [panel for panel in panels if not panel.startswith("##")]
        return panels

    def _get_aggregated_panels(self, customer_id: str, default_panels: set[str]) -> list[str]:
        """Check if the customer is collaborator for gene panel master list
        and if all default panels are included in the gene panel master list.
        If not, add gene panel combo and broad non-specific gene panels.
        Return an aggregated gene panel."""
        if GenePanelMasterList.is_customer_collaborator_and_panels_in_gene_panels_master_list(
            customer_id=customer_id, gene_panels=default_panels
        ):
            return GenePanelMasterList.get_panel_names()
        all_panels: set[str] = default_panels | GenePanelMasterList.get_non_specific_gene_panels()
        return sorted(all_panels)
