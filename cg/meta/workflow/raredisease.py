"""Module for Raredisease Analysis API."""

import logging
from pathlib import Path

from cg.constants import GenePanelMasterList, Workflow
from cg.constants.gene_panel import GENOME_BUILD_37
from cg.meta.workflow.analysis import add_gene_panel_combo
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase, MultiqcDataJson
from cg.io.json import read_json

LOG = logging.getLogger(__name__)


class RarediseaseAnalysisAPI(NfAnalysisAPI):
    """Handles communication between RAREDISEASE processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.RAREDISEASE,
    ):
        super().__init__(config=config, workflow=workflow)

    @property
    def root(self) -> str:
        return self.config.raredisease.root

    def write_managed_variants(self, case_id: str, content: list[str]) -> None:
        self._write_managed_variants(out_dir=Path(self.root, case_id), content=content)

    def write_panel(self, case_id: str, content: list[str]) -> None:
        """Write the gene panel to case dir."""
        self._write_panel(out_dir=Path(self.root, case_id), content=content)

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
        all_panels |= {GenePanelMasterList.OMIM_AUTO, GenePanelMasterList.PANELAPP_GREEN}
        return list(all_panels)

    def get_gene_panel(self, case_id: str) -> list[str]:
        """Create and return the aggregated gene panel file."""
        return self._get_gene_panel(case_id=case_id, genome_build=GENOME_BUILD_37)

    def get_managed_variants(self) -> list[str]:
        """Create and return the managed variants."""
        return self._get_managed_variants(genome_build=GENOME_BUILD_37)

    def get_multiqc_json_metrics(self, case_id: str) -> list[MetricsBase]:
        """Return a list of the metrics specified in a MultiQC json file for the case samples."""
        multiqc_json: list[dict] = MultiqcDataJson(
            **read_json(file_path=self.get_multiqc_json_path(case_id=case_id))
        ).report_general_stats_data
        samples: list[Sample] = self.status_db.get_samples_by_case_id(case_id=case_id)
        metrics_list: list[MetricsBase] = []
        for sample in samples:
            sample_id: str = sample.internal_id
            metrics_values: dict = self.parse_multiqc_json_for_sample(
                sample_name=sample.name, multiqc_json=multiqc_json
            )
            metric_base_list: list = self.get_metric_base_list(
                sample_id=sample_id, metrics_values=metrics_values
            )
            metrics_list.extend(metric_base_list)
        return metrics_list

    @staticmethod
    def parse_multiqc_json_for_sample(sample_name: str, multiqc_json: list[dict]) -> dict:
        """Parse a multiqc_data.json and returns a dictionary with metric name and metric values for each sample."""
        metrics_values: dict = {}
        for stat_dict in multiqc_json:
            for sample_key, sample_values in stat_dict.items():
                if sample_key == f"{sample_name}_{sample_name}":
                    LOG.info(f"Key: {sample_key}, Values: {sample_values}")
                    metrics_values.update(sample_values)

        return metrics_values
