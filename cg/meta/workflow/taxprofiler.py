"""Module for Taxprofiler Analysis API."""

import logging
from pathlib import Path
from typing import Any

from cg.constants import Workflow
from cg.constants.sequencing import SequencingPlatform
from cg.io.json import read_json
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase, MultiqcDataJson
from cg.models.fastq import FastqFileMeta
from cg.models.taxprofiler.taxprofiler import (
    TaxprofilerParameters,
    TaxprofilerSampleSheetEntry,
)
from cg.store.models import Case, Sample

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
        self.nfcore_workflow_path: str = config.taxprofiler.pipeline_path
        self.conda_env: str = config.taxprofiler.conda_env
        self.conda_binary: str = config.taxprofiler.conda_binary
        self.profile: str = config.taxprofiler.profile
        self.revision: str = config.taxprofiler.revision
        self.hostremoval_reference: Path = Path(config.taxprofiler.hostremoval_reference)
        self.databases: Path = Path(config.taxprofiler.databases)
        self.tower_binary_path: str = config.tower_binary_path
        self.tower_workflow: str = config.taxprofiler.tower_pipeline
        self.account: str = config.taxprofiler.slurm.account
        self.email: str = config.taxprofiler.slurm.mail_user
        self.nextflow_binary_path: str = config.taxprofiler.binary_path
        self.compute_env_base: str = config.taxprofiler.compute_env

    def get_sample_sheet_content_per_sample(
        self, sample: Sample, instrument_platform: SequencingPlatform.ILLUMINA, fasta: str = ""
    ) -> list[list[str]]:
        """Get sample sheet content per sample."""
        sample_name: str = sample.name
        sample_metadata: list[FastqFileMeta] = self.gather_file_metadata_for_sample(sample)
        fastq_forward_read_paths: list[str] = self.extract_read_files(
            metadata=sample_metadata, forward_read=True
        )
        fastq_reverse_read_paths: list[str] = self.extract_read_files(
            metadata=sample_metadata, reverse_read=True
        )
        sample_sheet_entry = TaxprofilerSampleSheetEntry(
            name=sample_name,
            run_accession=sample_name,
            instrument_platform=instrument_platform,
            fastq_forward_read_paths=fastq_forward_read_paths,
            fastq_reverse_read_paths=fastq_reverse_read_paths,
            fasta=fasta,
        )
        return sample_sheet_entry.reformat_sample_content()

    def get_sample_sheet_content(
        self,
        case_id: str,
        instrument_platform: SequencingPlatform.ILLUMINA,
        fasta: str = "",
    ) -> list[list[Any]]:
        """Write sample sheet for Taxprofiler analysis in case folder."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample_sheet_content = []
        LOG.info(f"Samples linked to case {case_id}: {len(case.links)}")
        LOG.debug("Getting sample sheet information")
        for link in case.links:
            sample_sheet_content.extend(
                self.get_sample_sheet_content_per_sample(
                    sample=link.sample, instrument_platform=instrument_platform, fasta=fasta
                )
            )
        return sample_sheet_content

    def get_workflow_parameters(self, case_id: str) -> TaxprofilerParameters:
        """Return Taxprofiler parameters."""
        LOG.debug("Getting parameters information")
        return TaxprofilerParameters(
            cluster_options=f"--qos={self.get_slurm_qos_for_case(case_id=case_id)}",
            sample_sheet_path=self.get_sample_sheet_path(case_id=case_id),
            outdir=self.get_case_path(case_id=case_id),
            databases=self.databases,
            hostremoval_reference=self.hostremoval_reference,
            priority=self.account,
        )

    def config_case(
        self,
        case_id: str,
        instrument_platform: SequencingPlatform.ILLUMINA,
        dry_run: bool,
        fasta: str = "",
    ) -> None:
        """Create sample sheet file and parameters file for Taxprofiler analysis."""
        self.create_case_directory(case_id=case_id, dry_run=dry_run)
        sample_sheet_content: list[list[Any]] = self.get_sample_sheet_content(
            case_id=case_id,
            instrument_platform=instrument_platform,
            fasta=fasta,
        )
        workflow_parameters: TaxprofilerParameters = self.get_workflow_parameters(case_id=case_id)
        if dry_run:
            LOG.info("Dry run: Config files will not be written")
            return
        self.write_sample_sheet(
            content=sample_sheet_content,
            file_path=self.get_sample_sheet_path(case_id=case_id),
            header=TaxprofilerSampleSheetEntry.headers(),
        )
        self.write_params_file(case_id=case_id, workflow_parameters=workflow_parameters.dict())

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
