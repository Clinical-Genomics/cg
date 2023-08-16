"""Module for Rnafusion Analysis API."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from pydantic.v1 import ValidationError

from cg import resources
from cg.constants import Pipeline
from cg.constants.constants import FileFormat
from cg.constants.nextflow import NFX_READ1_HEADER, NFX_READ2_HEADER, NFX_SAMPLE_HEADER
from cg.constants.rnafusion import (
    RNAFUSION_METRIC_CONDITIONS,
    RNAFUSION_SAMPLESHEET_HEADERS,
    RNAFUSION_STRANDEDNESS_HEADER,
)
from cg.constants.tb import AnalysisStatus
from cg.exc import CgError, MetricsQCError, MissingMetrics
from cg.io.controller import ReadFile, WriteFile
from cg.io.json import read_json
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import (
    MetricsBase,
    MetricsDeliverablesCondition,
    MultiqcDataJson,
)
from cg.models.nf_analysis import NextflowDeliverables, PipelineParameters
from cg.models.rnafusion.rnafusion import RnafusionAnalysis, RnafusionParameters, RnafusionSample
from cg.store.models import Family

LOG = logging.getLogger(__name__)


class RnafusionAnalysisAPI(NfAnalysisAPI):
    """Handles communication between RNAFUSION processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.RNAFUSION,
    ):
        super().__init__(config=config, pipeline=pipeline)
        self.root_dir: str = config.rnafusion.root
        self.nfcore_pipeline_path: str = config.rnafusion.pipeline_path
        self.references: str = config.rnafusion.references
        self.profile: str = config.rnafusion.profile
        self.conda_env: str = config.rnafusion.conda_env
        self.conda_binary: str = config.rnafusion.conda_binary
        self.tower_binary_path: str = config.rnafusion.tower_binary_path
        self.tower_pipeline: str = config.rnafusion.tower_pipeline
        self.account: str = config.rnafusion.slurm.account
        self.email: str = config.rnafusion.slurm.mail_user
        self.compute_env: str = config.rnafusion.compute_env
        self.revision: str = config.rnafusion.revision
        self.nextflow_binary_path: str = config.rnafusion.binary_path

    @staticmethod
    def build_samplesheet_content(
        case_id: str, fastq_forward: List[str], fastq_reverse: List[str], strandedness: str
    ) -> Dict[str, List[str]]:
        """Build samplesheet headers and lists"""
        try:
            RnafusionSample(
                sample=case_id,
                fastq_forward=fastq_forward,
                fastq_reverse=fastq_reverse,
                strandedness=strandedness,
            )
        except ValidationError as error:
            LOG.error(error)
            raise CgError("Error creating sample sheet")

        samples_full_list: list = []
        strandedness_full_list: list = []
        # Complete sample and strandedness lists to the same length as fastq_forward:
        for _ in range(len(fastq_forward)):
            samples_full_list.append(case_id)
            strandedness_full_list.append(strandedness)

        samplesheet_content: dict = {
            NFX_SAMPLE_HEADER: samples_full_list,
            NFX_READ1_HEADER: fastq_forward,
            NFX_READ2_HEADER: fastq_reverse,
            RNAFUSION_STRANDEDNESS_HEADER: strandedness_full_list,
        }
        return samplesheet_content

    def write_samplesheet(self, case_id: str, strandedness: str) -> None:
        """Write sample sheet for rnafusion analysis in case folder."""
        case: Family = self.status_db.get_case_by_internal_id(internal_id=case_id)
        if len(case.links) != 1:
            raise NotImplementedError(
                "Case objects are assumed to be related to a single sample (one link)"
            )

        for link in case.links:
            sample_metadata: List[dict] = self.gather_file_metadata_for_sample(link.sample)
            forward_read: List[str] = self.extract_read_files(
                metadata=sample_metadata, forward_read=True
            )
            reverse_read: List[str] = self.extract_read_files(
                metadata=sample_metadata, reverse_read=True
            )
            samplesheet_content: Dict[str, List[str]] = self.build_samplesheet_content(
                case_id, forward_read, reverse_read, strandedness
            )
            LOG.info(samplesheet_content)
            self.write_sample_sheet_csv(
                samplesheet_content=samplesheet_content,
                headers=RNAFUSION_SAMPLESHEET_HEADERS,
                config_path=self.get_case_config_path(case_id=case_id),
            )

    def get_pipeline_parameters(
        self, case_id: str, genomes_base: Optional[Path] = None
    ) -> PipelineParameters:
        """Get rnafusion parameters."""
        return RnafusionParameters(
            clusterOptions=f"--qos={self.get_slurm_qos_for_case(case_id=case_id)}",
            genomes_base=genomes_base or self.get_references_path(),
            input=self.get_case_config_path(case_id=case_id),
            outdir=self.get_case_path(case_id=case_id),
            priority=self.account,
        )

    def get_references_path(self, genomes_base: Optional[Path] = None) -> Path:
        if genomes_base:
            return genomes_base.absolute()
        return Path(self.references).absolute()

    def config_case(
        self,
        case_id: str,
        strandedness: str,
        genomes_base: Path,
        dry_run: bool,
    ) -> None:
        """Create sample sheet file for RNAFUSION analysis."""
        self.create_case_directory(case_id=case_id, dry_run=dry_run)
        LOG.info("Generating samplesheet")
        if dry_run:
            LOG.info("Dry run: Config files will not be written")
            return
        self.write_samplesheet(case_id=case_id, strandedness=strandedness)
        LOG.info("Generating parameters file")
        self.write_params_file(
            case_id=case_id,
            pipeline_parameters=self.get_pipeline_parameters(
                case_id=case_id, genomes_base=genomes_base
            ).dict(),
        )

        LOG.info("Configs files written")

    def report_deliver(self, case_id: str) -> None:
        """Get a deliverables file template from resources, parse it and, then write the deliverables file."""
        deliverables_content: dict = self.get_template_deliverables_file_content(
            resources.RNAFUSION_BUNDLE_FILENAMES_PATH
        )
        try:
            for index, deliver_file in enumerate(deliverables_content):
                NextflowDeliverables(deliverables=deliver_file)
                deliverables_content[index] = self.replace_dict_values(
                    self.get_replace_map(case_id=case_id),
                    deliver_file,
                )
        except ValidationError as error:
            LOG.error(error)
            raise ValueError
        self.create_case_directory(case_id=case_id)
        self.write_deliverables_bundle(
            deliverables_content=self.add_bundle_header(deliverables_content=deliverables_content),
            file_path=self.get_deliverables_file_path(case_id=case_id),
        )
        LOG.info(
            f"Writing deliverables file in {self.get_deliverables_file_path(case_id=case_id).as_posix()}"
        )

    def get_multiqc_json_path(self, case_id: str) -> Path:
        """Return the path of the multiqc_data.json file."""
        return Path(self.root_dir, case_id, "multiqc", "multiqc_data", "multiqc_data.json")

    def get_multiqc_json_metrics(self, case_id: str) -> List[MetricsBase]:
        """Get a multiqc_data.json file and returns metrics and values formatted."""
        case: Family = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample_id: str = case.links[0].sample.internal_id
        multiqc_json: MultiqcDataJson = MultiqcDataJson(
            **read_json(file_path=self.get_multiqc_json_path(case_id=case_id))
        )
        metrics_values: Dict = {}
        for key in multiqc_json.report_general_stats_data:
            if case_id in key:
                metrics_values.update(list(key.values())[0])
        return [
            MetricsBase(
                header=None,
                id=sample_id,
                input="multiqc_data.json",
                name=metric_name,
                step="multiqc",
                value=metric_value,
                condition=RNAFUSION_METRIC_CONDITIONS.get(metric_name, None),
            )
            for metric_name, metric_value in metrics_values.items()
        ]

    @staticmethod
    def ensure_mandatory_metrics_present(metrics: List[MetricsBase]) -> None:
        """Check that all mandatory metrics are present. Raise error if missing."""
        given_metrics: set = {metric.name for metric in metrics}
        mandatory_metrics: set = set(RNAFUSION_METRIC_CONDITIONS.keys())
        missing_metrics: set = mandatory_metrics.difference(given_metrics)
        if missing_metrics:
            LOG.error(f"Some mandatory metrics are missing: {', '.join(missing_metrics)}")
            raise MissingMetrics()

    def write_metrics_deliverables(self, case_id: str, dry_run: bool = False) -> None:
        """Write <case>_metrics_deliverables.yaml file."""
        metrics_deliverables_path: Path = self.get_metrics_deliverables_path(case_id=case_id)
        metrics = self.get_multiqc_json_metrics(case_id=case_id)
        self.ensure_mandatory_metrics_present(metrics=metrics)

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

    def validate_qc_metrics(self, case_id: str, dry_run: bool = False) -> None:
        """Validate the information from a qc metrics deliverable file."""

        if dry_run:
            LOG.info("Dry-run: QC metrics validation would be performed")
            return

        LOG.info("Validating QC metrics")
        try:
            metrics_deliverables_path: Path = self.get_metrics_deliverables_path(case_id=case_id)
            qc_metrics_raw: dict = ReadFile.get_content_from_file(
                file_format=FileFormat.YAML, file_path=metrics_deliverables_path
            )
            MetricsDeliverablesCondition(**qc_metrics_raw)
        except MetricsQCError as error:
            LOG.error(f"QC metrics failed for {case_id}")
            self.trailblazer_api.set_analysis_status(case_id=case_id, status=AnalysisStatus.FAILED)
            self.trailblazer_api.add_comment(case_id=case_id, comment=str(error))
            raise MetricsQCError from error
        except CgError as error:
            LOG.error(f"Could not create metrics deliverables file: {error}")
            self.trailblazer_api.set_analysis_status(case_id=case_id, status=AnalysisStatus.ERROR)
            raise CgError from error
        self.trailblazer_api.set_analysis_status(case_id=case_id, status=AnalysisStatus.COMPLETED)

    def parse_analysis(self, qc_metrics_raw: List[MetricsBase], **kwargs) -> RnafusionAnalysis:
        """Parse Rnafusion output analysis files and return analysis model."""
        sample_metrics: Dict[str, dict] = {}
        for metric in qc_metrics_raw:
            metric.name = metric.name.replace("5_3_bias", "bias_5_3")
            try:
                sample_metrics[metric.id].update({metric.name.lower(): metric.value})
            except KeyError:
                sample_metrics[metric.id] = {metric.name.lower(): metric.value}
        return RnafusionAnalysis(sample_metrics=sample_metrics)

    def get_latest_metadata(self, case_id: str) -> RnafusionAnalysis:
        """Return the latest metadata of a specific Rnafusion case."""
        qc_metrics: List[MetricsBase] = self.get_multiqc_json_metrics(case_id)
        return self.parse_analysis(qc_metrics_raw=qc_metrics)
