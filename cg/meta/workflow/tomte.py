"""Module for Tomte Analysis API."""

import logging
from pathlib import Path

from cg.constants import Workflow
from cg.constants.constants import GenomeVersion
from cg.constants.nf_analysis import TOMTE_METRIC_CONDITIONS
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase
from cg.models.tomte.tomte import TomteQCMetrics
from cg.resources import TOMTE_BUNDLE_FILENAMES_PATH

LOG = logging.getLogger(__name__)


class TomteAnalysisAPI(NfAnalysisAPI):
    """Handles communication between Tomte processes and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.TOMTE,
    ):
        super().__init__(config=config, workflow=workflow)
        self.root_dir: str = config.tomte.root
        self.workflow_bin_path: str = config.tomte.workflow_bin_path
        self.profile: str = config.tomte.profile
        self.conda_env: str = config.tomte.conda_env
        self.conda_binary: str = config.tomte.conda_binary
        self.platform: str = config.tomte.platform
        self.params: str = config.tomte.params
        self.workflow_config_path: str = config.tomte.config
        self.resources: str = config.tomte.resources
        self.tower_binary_path: str = config.tower_binary_path
        self.tower_workflow: str = config.tomte.tower_workflow
        self.account: str = config.tomte.slurm.account
        self.email: str = config.tomte.slurm.mail_user
        self.revision: str = config.tomte.revision
        self.nextflow_binary_path: str = config.tomte.binary_path

    @staticmethod
    def get_bundle_filenames_path() -> Path:
        """Return path to bundle template."""
        return TOMTE_BUNDLE_FILENAMES_PATH

    def get_genome_build(self, case_id: str) -> str:
        return GenomeVersion.HG38

    def get_workflow_metrics(self, metric_id: str) -> dict:
        return TOMTE_METRIC_CONDITIONS

    def parse_analysis(self, qc_metrics_raw: list[MetricsBase], **kwargs) -> NextflowAnalysis:
        """Parse Nextflow output analysis files and return an analysis model."""
        qc_metrics_model = TomteQCMetrics
        return super().parse_analysis(
            qc_metrics_raw=qc_metrics_raw, qc_metrics_model=qc_metrics_model, **kwargs
        )
