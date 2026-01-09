"""Module for Rnafusion Analysis API."""

import logging
from pathlib import Path

from cg.constants import Workflow
from cg.constants.constants import GenomeVersion
from cg.constants.nf_analysis import RNAFUSION_METRIC_CONDITIONS
from cg.constants.scout import RNAFUSION_CASE_TAGS
from cg.exc import MissingMetrics
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase
from cg.models.rnafusion.rnafusion import RnafusionQCMetrics
from cg.resources import RNAFUSION_BUNDLE_FILENAMES_PATH

LOG = logging.getLogger(__name__)


class RnafusionAnalysisAPI(NfAnalysisAPI):
    """Handles communication between RNAFUSION processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.RNAFUSION,
    ):
        super().__init__(config=config, workflow=workflow)
        self.root_dir: str = config.rnafusion.root
        self.workflow_bin_path: str = config.rnafusion.workflow_bin_path
        self.profile: str = config.rnafusion.profile
        self.conda_env: str = config.rnafusion.conda_env
        self.conda_binary: str = config.rnafusion.conda_binary
        self.platform: str = config.rnafusion.platform
        self.params: str = config.rnafusion.params
        self.workflow_config_path: str = config.rnafusion.config
        self.resources: str = config.rnafusion.resources
        self.tower_binary_path: str = config.tower_binary_path
        self.tower_workflow: str = config.rnafusion.tower_workflow
        self.account: str = config.rnafusion.slurm.account
        self.email: str = config.rnafusion.slurm.mail_user
        self.revision: str = config.rnafusion.revision

    @property
    def is_multiple_samples_allowed(self) -> bool:
        """Return whether the analysis supports multiple samples to be linked to the case."""
        return False

    def get_genome_build(self, case_id: str) -> GenomeVersion:
        """Return reference genome for a case. Currently fixed for hg38."""
        return GenomeVersion.HG38

    @staticmethod
    def get_bundle_filenames_path() -> Path:
        """Return Rnafusion bundle filenames path."""
        return RNAFUSION_BUNDLE_FILENAMES_PATH

    @staticmethod
    def ensure_mandatory_metrics_present(metrics: list[MetricsBase]) -> None:
        """Check that all mandatory metrics are present.
        Raise: MissingMetrics if mandatory metrics are missing."""
        given_metrics: set = {metric.name for metric in metrics}
        mandatory_metrics: set = set(RNAFUSION_METRIC_CONDITIONS.keys())
        LOG.info("Mandatory Metrics Keys:")
        for key in mandatory_metrics:
            LOG.info(key)
        missing_metrics: set = mandatory_metrics.difference(given_metrics)
        if missing_metrics:
            LOG.error(f"Some mandatory metrics are missing: {', '.join(missing_metrics)}")
            raise MissingMetrics()

    def get_workflow_metrics(self, metric_id: str) -> dict:
        return RNAFUSION_METRIC_CONDITIONS

    def get_scout_upload_case_tags(self) -> dict:
        """Return Rnafusion Scout upload case tags."""
        return RNAFUSION_CASE_TAGS

    def parse_analysis(self, qc_metrics_raw: list[MetricsBase], **kwargs) -> NextflowAnalysis:
        """Parse Nextflow output analysis files and return an analysis model."""
        qc_metrics_model = RnafusionQCMetrics
        return super().parse_analysis(
            qc_metrics_raw=qc_metrics_raw, qc_metrics_model=qc_metrics_model, **kwargs
        )
