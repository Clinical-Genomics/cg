"""Module for Taxprofiler Analysis API."""

import logging
from pathlib import Path
from typing import Any, Optional

from cg.constants import Pipeline
from cg.constants.sequencing import SequencingPlatform
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.taxprofiler.taxprofiler import (
    TaxprofilerParameters,
    TaxprofilerSampleSheetEntry,
)
from cg.store.models import Case, Sample
from cg.io.controller import ReadFile, WriteFile
from cg.constants.constants import FileFormat
from cg.constants.metric_conditions import TAXPROFILER_METRIC_CONDITIONS
from cg.models.deliverables.metric_deliverables import (
    MetricsBase,
    MultiqcDataJson,
)
from cg.io.json import read_json

LOG = logging.getLogger(__name__)


class TaxprofilerAnalysisAPI(NfAnalysisAPI):
    """Handles communication between Taxprofiler processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.TAXPROFILER,
    ):
        super().__init__(config=config, pipeline=pipeline)
        self.root_dir: str = config.taxprofiler.root
        self.nfcore_pipeline_path: str = config.taxprofiler.pipeline_path
        self.conda_env: str = config.taxprofiler.conda_env
        self.conda_binary: str = config.taxprofiler.conda_binary
        self.profile: str = config.taxprofiler.profile
        self.revision: str = config.taxprofiler.revision
        self.hostremoval_reference: Path = Path(config.taxprofiler.hostremoval_reference)
        self.databases: Path = Path(config.taxprofiler.databases)
        self.tower_binary_path: str = config.taxprofiler.tower_binary_path
        self.tower_pipeline: str = config.taxprofiler.tower_pipeline
        self.account: str = config.taxprofiler.slurm.account
        self.email: str = config.taxprofiler.slurm.mail_user
        self.nextflow_binary_path: str = config.taxprofiler.binary_path

    def get_sample_sheet_content_per_sample(
        self, sample: Sample, instrument_platform: SequencingPlatform.ILLUMINA, fasta: str = ""
    ) -> list[list[str]]:
        """Get sample sheet content per sample."""
        sample_name: str = sample.name
        sample_metadata: list[str] = self.gather_file_metadata_for_sample(sample)
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

    def get_pipeline_parameters(self, case_id: str) -> TaxprofilerParameters:
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
        pipeline_parameters: TaxprofilerParameters = self.get_pipeline_parameters(case_id=case_id)
        if dry_run:
            LOG.info("Dry run: Config files will not be written")
            return
        self.write_sample_sheet(
            content=sample_sheet_content,
            file_path=self.get_sample_sheet_path(case_id=case_id),
            header=TaxprofilerSampleSheetEntry.headers(),
        )
        self.write_params_file(case_id=case_id, pipeline_parameters=pipeline_parameters.dict())

    def get_multiqc_per_sample(
        self, case_id: str, sample: Sample, pipeline_metrics: Optional[dict] = None
    ) -> list[MetricsBase]:
        """Get MultiQC values per sample."""
        sample_name: str = sample.name
        multiqc_json: MultiqcDataJson = MultiqcDataJson(
            **read_json(file_path=self.get_multiqc_json_path(case_id=case_id))
        )
        metrics_values: dict = {}
        for key in multiqc_json.report_general_stats_data:
            if sample_name + "_" + sample_name in key:
                metrics_values[sample].update(list(key.values())[0])
                LOG.info(f"Key: {key}, Values: {list(key.values())[0]}")

        return [
            MetricsBase(
                header=None,
                id=sample_name,
                input="multiqc_data.json",
                name=metric_name,
                step="multiqc",
                value=metric_value,
                condition=pipeline_metrics.get(metric_name, None),
            )
            for metric_name, metric_value in metrics_values.items()
        ]

    def write_metrics_deliverables(self, case_id: str, dry_run: bool = False) -> None:
        """Write <case>_metrics_deliverables.yaml file."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        metrics_deliverables_path: Path = self.get_metrics_deliverables_path(case_id=case_id)
        LOG.info("Case " + str(case))
        for link in case.links:
            metrics = self.get_multiqc_per_sample(
                case_id=case_id, sample=link.sample, pipeline_metrics=TAXPROFILER_METRIC_CONDITIONS
            )
        if dry_run:
            LOG.info(
                f"Dry-run: metrics deliverables file would be written to {metrics_deliverables_path.as_posix()}"
            )
            return

        LOG.info(f"Writing metrics deliverables file to {metrics_deliverables_path.as_posix()}")
        WriteFile.write_file_from_content(
            content={"metrics": [metric.dict() for metric in metrics]},
            file_format=FileFormat.YAML,
            file_path=metrics_deliverables_path,
        )
