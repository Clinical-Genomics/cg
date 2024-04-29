"""Module for Taxprofiler Analysis API."""

import logging
from pathlib import Path

from cg.constants import Workflow
from cg.constants.nf_analysis import MULTIQC_NEXFLOW_CONFIG
from cg.constants.sequencing import SequencingPlatform
from cg.constants.symbols import EMPTY_STRING
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.taxprofiler.taxprofiler import TaxprofilerParameters, TaxprofilerSampleSheetEntry
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
        self.nfcore_workflow_path: str = config.taxprofiler.workflow_path
        self.conda_env: str = config.taxprofiler.conda_env
        self.conda_binary: str = config.taxprofiler.conda_binary
        self.profile: str = config.taxprofiler.profile
        self.revision: str = config.taxprofiler.revision
        self.hostremoval_reference: Path = Path(config.taxprofiler.hostremoval_reference)
        self.databases: Path = Path(config.taxprofiler.databases)
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
    def is_params_appended_to_nextflow_config(self) -> bool:
        """Return True if parameters should be added into the nextflow config file instead of the params file."""
        return False

    @property
    def is_multiqc_pattern_search_exact(self) -> bool:
        """Only exact pattern search is allowed to collect metrics information from multiqc file."""
        return True

    def get_nextflow_config_content(self, case_id: str) -> str:
        """Return nextflow config content."""
        return MULTIQC_NEXFLOW_CONFIG

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

    def get_workflow_parameters(self, case_id: str) -> TaxprofilerParameters:
        """Return Taxprofiler parameters."""
        return TaxprofilerParameters(
            cluster_options=f"--qos={self.get_slurm_qos_for_case(case_id=case_id)}",
            input=self.get_sample_sheet_path(case_id=case_id),
            outdir=self.get_case_path(case_id=case_id),
            databases=self.databases,
            hostremoval_reference=self.hostremoval_reference,
            priority=self.account,
        )

    def get_multiqc_search_patterns(self, case_id: str) -> dict:
        """Return search patterns for MultiQC for Taxprofiler."""
        samples: list[Sample] = self.status_db.get_samples_by_case_id(case_id=case_id)
        search_patterns: dict[str, str] = {
            f"{sample.name}_{sample.name}": sample.internal_id for sample in samples
        }
        return search_patterns
