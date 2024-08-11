"""Module for Rnafusion Analysis API."""

import logging
from pathlib import Path

from cg.constants import Workflow
from cg.constants.constants import GenomeVersion, Strandedness
from cg.constants.nf_analysis import MULTIQC_NEXFLOW_CONFIG, RNAFUSION_METRIC_CONDITIONS
from cg.constants.scout import RNAFUSION_CASE_TAGS
from cg.exc import MissingMetrics
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase
from cg.models.rnafusion.rnafusion import RnafusionParameters, RnafusionSampleSheetEntry
from cg.resources import RNAFUSION_BUNDLE_FILENAMES_PATH
from cg.store.models import CaseSample

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
        self.nfcore_workflow_path: str = config.rnafusion.workflow_path
        self.references: str = config.rnafusion.references
        self.profile: str = config.rnafusion.profile
        self.conda_env: str = config.rnafusion.conda_env
        self.conda_binary: str = config.rnafusion.conda_binary
        self.tower_binary_path: str = config.tower_binary_path
        self.tower_workflow: str = config.rnafusion.tower_workflow
        self.account: str = config.rnafusion.slurm.account
        self.email: str = config.rnafusion.slurm.mail_user
        self.compute_env_base: str = config.rnafusion.compute_env
        self.revision: str = config.rnafusion.revision
        self.nextflow_binary_path: str = config.rnafusion.binary_path

    @property
    def sample_sheet_headers(self) -> list[str]:
        """Headers for sample sheet."""
        return RnafusionSampleSheetEntry.headers()

    @property
    def is_params_appended_to_nextflow_config(self) -> bool:
        """Return True if parameters should be added into the nextflow config file instead of the params file."""
        return False

    @property
    def is_multiple_samples_allowed(self) -> bool:
        """Return whether the analysis supports multiple samples to be linked to the case."""
        return False

    def get_genome_build(self, case_id: str) -> GenomeVersion:
        """Return reference genome for a case. Currently fixed for hg38."""
        return GenomeVersion.HG38

    def get_nextflow_config_content(self, case_id: str) -> str:
        """Return nextflow config content."""
        return MULTIQC_NEXFLOW_CONFIG

    @staticmethod
    def get_bundle_filenames_path() -> Path:
        """Return Rnafusion bundle filenames path."""
        return RNAFUSION_BUNDLE_FILENAMES_PATH

    def get_sample_sheet_content_per_sample(self, case_sample: CaseSample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        fastq_forward_read_paths, fastq_reverse_read_paths = self.get_paired_read_paths(
            sample=case_sample.sample
        )
        sample_sheet_entry = RnafusionSampleSheetEntry(
            name=case_sample.sample.internal_id,
            fastq_forward_read_paths=fastq_forward_read_paths,
            fastq_reverse_read_paths=fastq_reverse_read_paths,
            strandedness=Strandedness.REVERSE,
        )
        return sample_sheet_entry.reformat_sample_content()

    def get_workflow_parameters(
        self, case_id: str, genomes_base: Path | None = None
    ) -> RnafusionParameters:
        """Get Rnafusion parameters."""
        return RnafusionParameters(
            cluster_options=f"--qos={self.get_slurm_qos_for_case(case_id=case_id)}",
            genomes_base=genomes_base or self.get_references_path(),
            input=self.get_sample_sheet_path(case_id=case_id),
            outdir=self.get_case_path(case_id=case_id),
            priority=self.account,
        )

    def get_references_path(self, genomes_base: Path | None = None) -> Path:
        if genomes_base:
            return genomes_base.absolute()
        return Path(self.references).absolute()

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
