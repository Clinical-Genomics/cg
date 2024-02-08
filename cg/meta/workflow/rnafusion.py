"""Module for Rnafusion Analysis API."""

import logging
from pathlib import Path
from typing import Any

from cg import resources
from cg.constants import Workflow
from cg.constants.constants import FileFormat, Strandedness
from cg.constants.nf_analysis import RNAFUSION_METRIC_CONDITIONS
from cg.exc import MissingMetrics
from cg.io.controller import ReadFile
from cg.io.json import read_json
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase, MultiqcDataJson
from cg.models.fastq import FastqFileMeta
from cg.models.nf_analysis import PipelineDeliverables
from cg.models.rnafusion.rnafusion import (
    RnafusionAnalysis,
    RnafusionParameters,
    RnafusionSampleSheetEntry,
)
from cg.store.models import Case, Sample

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
        self.nfcore_workflow_path: str = config.rnafusion.pipeline_path
        self.references: str = config.rnafusion.references
        self.profile: str = config.rnafusion.profile
        self.conda_env: str = config.rnafusion.conda_env
        self.conda_binary: str = config.rnafusion.conda_binary
        self.tower_binary_path: str = config.tower_binary_path
        self.tower_workflow: str = config.rnafusion.tower_pipeline
        self.account: str = config.rnafusion.slurm.account
        self.email: str = config.rnafusion.slurm.mail_user
        self.compute_env_base: str = config.rnafusion.compute_env
        self.revision: str = config.rnafusion.revision
        self.nextflow_binary_path: str = config.rnafusion.binary_path

    @property
    def use_read_count_threshold(self) -> bool:
        """Defines whether the threshold for adequate read count should be passed for all samples
        when determining if the analysis for a case should be automatically started."""
        return True

    @staticmethod
    def get_deliverables_template_content() -> list[dict]:
        """Return deliverables file template content."""
        return ReadFile.get_content_from_file(
            file_format=FileFormat.YAML,
            file_path=resources.RNAFUSION_BUNDLE_FILENAMES_PATH,
        )

    def get_sample_sheet_content_per_sample(
        self, sample: Sample, case_id: str, strandedness: Strandedness
    ) -> list[list[str]]:
        """Get sample sheet content per sample."""
        sample_metadata: list[FastqFileMeta] = self.gather_file_metadata_for_sample(sample=sample)
        fastq_forward_read_paths: list[str] = self.extract_read_files(
            metadata=sample_metadata, forward_read=True
        )
        fastq_reverse_read_paths: list[str] = self.extract_read_files(
            metadata=sample_metadata, reverse_read=True
        )

        sample_sheet_entry = RnafusionSampleSheetEntry(
            name=case_id,
            fastq_forward_read_paths=fastq_forward_read_paths,
            fastq_reverse_read_paths=fastq_reverse_read_paths,
            strandedness=strandedness,
        )
        return sample_sheet_entry.reformat_sample_content()

    def get_sample_sheet_content(self, case_id: str, strandedness: Strandedness) -> list[list[Any]]:
        """Returns content for sample sheet."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        if len(case.links) != 1:
            raise NotImplementedError(
                "Case objects are assumed to be related to a single sample (one link)"
            )
        LOG.debug("Getting sample sheet information")
        for link in case.links:
            content_per_sample = self.get_sample_sheet_content_per_sample(
                sample=link.sample, case_id=case_id, strandedness=strandedness
            )
            return content_per_sample

    def get_workflow_parameters(
        self, case_id: str, genomes_base: Path | None = None
    ) -> RnafusionParameters:
        """Get Rnafusion parameters."""
        LOG.debug("Getting parameters information")
        return RnafusionParameters(
            cluster_options=f"--qos={self.get_slurm_qos_for_case(case_id=case_id)}",
            genomes_base=genomes_base or self.get_references_path(),
            sample_sheet_path=self.get_sample_sheet_path(case_id=case_id),
            outdir=self.get_case_path(case_id=case_id),
            priority=self.account,
        )

    def get_references_path(self, genomes_base: Path | None = None) -> Path:
        if genomes_base:
            return genomes_base.absolute()
        return Path(self.references).absolute()

    def config_case(
        self,
        case_id: str,
        strandedness: Strandedness,
        genomes_base: Path,
        dry_run: bool,
    ) -> None:
        """Create config files (parameters and sample sheet) for Rnafusion analysis."""
        self.create_case_directory(case_id=case_id, dry_run=dry_run)
        sample_sheet_content: list[list[Any]] = self.get_sample_sheet_content(
            case_id=case_id, strandedness=strandedness
        )
        workflow_parameters: RnafusionParameters = self.get_workflow_parameters(
            case_id=case_id, genomes_base=genomes_base
        )
        if dry_run:
            LOG.info("Dry run: Config files will not be written")
            return
        self.write_sample_sheet(
            content=sample_sheet_content,
            file_path=self.get_sample_sheet_path(case_id=case_id),
            header=RnafusionSampleSheetEntry.headers(),
        )
        self.write_params_file(case_id=case_id, workflow_parameters=workflow_parameters.dict())

    def parse_multiqc_json_for_case(self, case_id: str) -> dict:
        """Parse a multiqc_data.json file and returns a dictionary with metric name and metric values for a case."""
        multiqc_json = MultiqcDataJson(
            **read_json(file_path=self.get_multiqc_json_path(case_id=case_id))
        )
        metrics_values: dict = {}
        for key in multiqc_json.report_general_stats_data:
            if case_id in key:
                metrics_values.update(list(key.values())[0])
                LOG.info(f"Key: {key}, Values: {list(key.values())[0]}")
        return metrics_values

    def get_multiqc_json_metrics(self, case_id: str) -> list[MetricsBase]:
        """Get a multiqc_data.json file and returns metrics and values formatted."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample_id: str = case.links[0].sample.internal_id
        metric_values: dict = self.parse_multiqc_json_for_case(case_id=case_id)
        metric_base_list: list = self.get_metric_base_list(
            sample_id=sample_id, metrics_values=metric_values
        )
        return metric_base_list

    def report_deliver(self, case_id: str) -> None:
        """Create deliverables file."""
        deliverables_content: PipelineDeliverables = self.get_deliverables_for_case(case_id=case_id)
        self.write_deliverables_file(
            deliverables_content=deliverables_content.dict(),
            file_path=self.get_deliverables_file_path(case_id=case_id),
        )
        LOG.info(
            f"Writing deliverables file in {self.get_deliverables_file_path(case_id=case_id).as_posix()}"
        )

    @staticmethod
    def ensure_mandatory_metrics_present(metrics: list[MetricsBase]) -> None:
        """Check that all mandatory metrics are present. Raise error if missing."""
        given_metrics: set = {metric.name for metric in metrics}
        mandatory_metrics: set = set(RNAFUSION_METRIC_CONDITIONS.keys())
        LOG.info("Mandatory Metrics Keys:")
        for key in mandatory_metrics:
            LOG.info(key)
        missing_metrics: set = mandatory_metrics.difference(given_metrics)
        if missing_metrics:
            LOG.error(f"Some mandatory metrics are missing: {', '.join(missing_metrics)}")
            raise MissingMetrics()

    def parse_analysis(self, qc_metrics_raw: list[MetricsBase], **kwargs) -> RnafusionAnalysis:
        """Parse Rnafusion output analysis files and return analysis model."""
        sample_metrics: dict[str, dict] = {}
        for metric in qc_metrics_raw:
            try:
                sample_metrics[metric.id].update({metric.name.lower(): metric.value})
            except KeyError:
                sample_metrics[metric.id] = {metric.name.lower(): metric.value}
        return RnafusionAnalysis(sample_metrics=sample_metrics)

    def get_latest_metadata(self, case_id: str) -> RnafusionAnalysis:
        """Return the latest metadata of a specific Rnafusion case."""
        qc_metrics: list[MetricsBase] = self.get_multiqc_json_metrics(case_id)
        return self.parse_analysis(qc_metrics_raw=qc_metrics)

    def get_workflow_metrics(self) -> dict:
        return RNAFUSION_METRIC_CONDITIONS
