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

LOG = logging.getLogger(__name__)


class TomteAnalysisAPI(NfAnalysisAPI):
    """Handles communication between Tomte processes and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.TOMTE,
    ):
        super().__init__(config=config, workflow=workflow)
        self.account: str = config.tomte.slurm.account
        self.bundle_filenames: str = config.tomte.bundle_filenames
        self.conda_binary: str = config.tomte.conda_binary
        self.conda_env: str = config.tomte.conda_env
        self.email: str = config.tomte.slurm.mail_user
        self.params: str = config.tomte.params
        self.platform: str = config.tomte.platform
        self.profile: str = config.tomte.profile
        self.resources: str = config.tomte.resources
        self.revision: str = config.tomte.revision
        self.root_dir: str = config.tomte.root
        self.tower_binary_path: str = config.tower_binary_path
        self.tower_workflow: str = config.tomte.tower_workflow
        self.workflow_bin_path: str = config.tomte.workflow_bin_path
        self.workflow_config_path: str = config.tomte.config

    @property
    def bundle_filenames_path(self) -> Path:
        return Path(self.bundle_filenames)

    def get_genome_build(self, case_id: str) -> str:
        return GenomeVersion.HG38

    def get_qc_conditions_for_workflow(self, sample_id: str) -> dict:
        return TOMTE_METRIC_CONDITIONS

    def parse_analysis(self, qc_metrics_raw: list[MetricsBase], **kwargs) -> NextflowAnalysis:
        """Parse Nextflow output analysis files and return an analysis model."""
        qc_metrics_model = TomteQCMetrics
        return super().parse_analysis(
            qc_metrics_raw=qc_metrics_raw, qc_metrics_model=qc_metrics_model, **kwargs
        )
