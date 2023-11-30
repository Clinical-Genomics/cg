"""Module for Raredisease Analysis API."""

import logging
from pathlib import Path

from cg.constants import GenePanelMasterList, Pipeline
from cg.constants.gene_panel import GENOME_BUILD_38
from cg.meta.workflow.analysis import add_gene_panel_combo
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case

LOG = logging.getLogger(__name__)


class RarediseaseAnalysisAPI(NfAnalysisAPI):
    """Handles communication between RAREDISEASE processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.RAREDISEASE,
    ):
        super().__init__(config=config, pipeline=pipeline)

    def write_panel(self, case_id: str, content: list[str]):
        """Write the gene panel to case dir"""
        out_dir = Path(self.root, case_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = Path(out_dir, "gene_panels.bed")
        with out_path.open("w") as out_handle:
            out_handle.write("\n".join(content))

    @staticmethod
    def get_aggregated_panels(customer_id: str, default_panels: set[str]) -> list[str]:
        """Check if customer should use the gene panel master list
        and if all default panels are included in the gene panel master list.
        If not, add gene panel combo and OMIM-AUTO.
        Return an aggregated gene panel."""
        master_list: list[str] = GenePanelMasterList.get_panel_names()
        if customer_id in GenePanelMasterList.collaborators() and default_panels.issubset(
            master_list
        ):
            return master_list
        all_panels: set[str] = add_gene_panel_combo(default_panels=default_panels)
        all_panels.add(GenePanelMasterList.OMIM_AUTO)
        return list(all_panels)

    def get_gene_panel(self, case_id: str, genome_build: str = GENOME_BUILD_38) -> list[str]:
        """Create and return the aggregated gene panel file."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        all_panels: list[str] = self.get_aggregated_panels(
            customer_id=case.customer.internal_id, default_panels=set(case.panels)
        )
        return self.scout_api.export_panels(build=genome_build, panels=all_panels)
