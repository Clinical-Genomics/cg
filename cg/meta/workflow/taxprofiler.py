"""Module for Taxprofiler Analysis API."""

import logging
from pathlib import Path

from cg.constants import Workflow
from cg.constants.constants import GenomeVersion
from cg.constants.sequencing import SequencingPlatform
from cg.constants.symbols import EMPTY_STRING
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase
from cg.models.taxprofiler.taxprofiler import (
    TaxprofilerParameters,
    TaxprofilerQCMetrics,
    TaxprofilerSampleSheetEntry,
)
from cg.resources import TAXPROFILER_BUNDLE_FILENAMES_PATH
from cg.store.models import CaseSample, Sample

LOG = logging.getLogger(__name__)


class TaxprofilerAnalysisAPI(NfAnalysisAPI):
    """Handles communication between Taxprofiler processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.TAXPROFILER,
    ):
        super().__init__(config=config, workflow=workflow)
        self.root_dir: str = config.taxprofiler.root
        self.workflow_bin_path: str = config.taxprofiler.workflow_bin_path
        self.profile: str = config.taxprofiler.profile
        self.conda_env: str = config.taxprofiler.conda_env
        self.conda_binary: str = config.taxprofiler.conda_binary
        self.platform: str = config.taxprofiler.platform
        self.params: str = config.taxprofiler.params
        self.workflow_config_path: str = config.taxprofiler.config
        self.resources: str = config.taxprofiler.resources
        self.revision: str = config.taxprofiler.revision
        self.tower_binary_path: str = config.tower_binary_path
        self.tower_workflow: str = config.taxprofiler.tower_workflow
        self.account: str = config.taxprofiler.slurm.account
        self.email: str = config.taxprofiler.slurm.mail_user
        self.nextflow_binary_path: str = config.taxprofiler.binary_path
        self.compute_env_base: str = config.taxprofiler.compute_env

    @property
    def sample_sheet_headers(self) -> list[str]:
        """Headers for sample sheet."""
        return TaxprofilerSampleSheetEntry.headers()

    @property
    def is_multiqc_pattern_search_exact(self) -> bool:
        """Only exact pattern search is allowed to collect metrics information from multiqc file."""
        return True

    @staticmethod
    def get_bundle_filenames_path() -> Path:
        """Return Taxprofiler bundle filenames path."""
        return TAXPROFILER_BUNDLE_FILENAMES_PATH

    def get_sample_sheet_content_per_sample(self, case_sample: CaseSample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        sample_name: str = case_sample.sample.name
        fastq_forward_read_paths, fastq_reverse_read_paths = self.get_paired_read_paths(
            sample=case_sample.sample
        )
        sample_sheet_entry = TaxprofilerSampleSheetEntry(
            name=sample_name,
            run_accession=sample_name,
            instrument_platform=SequencingPlatform.ILLUMINA,
            fastq_forward_read_paths=fastq_forward_read_paths,
            fastq_reverse_read_paths=fastq_reverse_read_paths,
            fasta=EMPTY_STRING,
        )
        return sample_sheet_entry.reformat_sample_content()

    def get_built_workflow_parameters(
        self, case_id: str, dry_run: bool = False
    ) -> TaxprofilerParameters:
        """Return Taxprofiler parameters."""
        return TaxprofilerParameters(
            input=self.get_sample_sheet_path(case_id=case_id),
            outdir=self.get_case_path(case_id=case_id),
        )

    def get_multiqc_search_patterns(self, case_id: str) -> dict:
        """Return search patterns for MultiQC for Taxprofiler."""
        samples: list[Sample] = self.status_db.get_samples_by_case_id(case_id=case_id)
        search_patterns: dict[str, str] = {
            f"{sample.name}_{sample.name}": sample.internal_id for sample in samples
        }
        return search_patterns

    def get_genome_build(self, case_id: str) -> str:
        """Return the reference genome build version of a Taxprofiler analysis."""
        return GenomeVersion.T2T_CHM13.value

    def parse_analysis(self, qc_metrics_raw: list[MetricsBase], **kwargs) -> NextflowAnalysis:
        """Parse Nextflow output analysis files and return an analysis model."""
        qc_metrics_model = TaxprofilerQCMetrics
        return super().parse_analysis(
            qc_metrics_raw=qc_metrics_raw, qc_metrics_model=qc_metrics_model, **kwargs
        )
