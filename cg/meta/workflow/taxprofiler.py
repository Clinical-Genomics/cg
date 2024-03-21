"""Module for Taxprofiler Analysis API."""

import logging
from pathlib import Path
from typing import Any

from cg.constants import Workflow
from cg.constants.constants import FileFormat
from cg.constants.nf_analysis import MULTIQC_NEXFLOW_CONFIG
from cg.constants.sequencing import SequencingPlatform
from cg.constants.symbols import EMPTY_STRING
from cg.io.controller import ReadFile
from cg.io.json import read_json
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase, MultiqcDataJson
from cg.models.fastq import FastqFileMeta
from cg.models.taxprofiler.taxprofiler import TaxprofilerParameters, TaxprofilerSampleSheetEntry
from cg.resources import TAXPROFILER_BUNDLE_FILENAMES_PATH
from cg.store.models import Case, CaseSample, Sample

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
    def is_multiple_samples_allowed(self) -> bool:
        """Return whether the analysis supports multiple samples to be linked to the case."""
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

    def get_deliverables_template_content(self) -> list[dict[str, str]]:
        """Return deliverables file template content."""
        return ReadFile.get_content_from_file(
            file_format=FileFormat.YAML,
            file_path=self.get_bundle_filenames_path(),
        )
