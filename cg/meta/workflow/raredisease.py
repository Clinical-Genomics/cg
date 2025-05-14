"""Module for Raredisease Analysis API."""

import csv
import logging
from itertools import permutations
from pathlib import Path
from typing import Any

from housekeeper.store.models import File

from cg.clients.chanjo2.models import (
    CoverageMetrics,
    CoveragePostRequest,
    CoveragePostResponse,
    CoverageSample,
)
from cg.constants import Workflow
from cg.constants.constants import GenomeVersion
from cg.constants.nf_analysis import (
    RAREDISEASE_COVERAGE_FILE_TAGS,
    RAREDISEASE_COVERAGE_INTERVAL_TYPE,
    RAREDISEASE_COVERAGE_THRESHOLD,
    RAREDISEASE_METRIC_CONDITIONS_WES,
    RAREDISEASE_METRIC_CONDITIONS_WGS,
    RAREDISEASE_PARENT_PEDDY_METRIC_CONDITION,
)
from cg.constants.scout import RAREDISEASE_CASE_TAGS, ScoutExportFileName
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.constants.subject import PlinkPhenotypeStatus, PlinkSex
from cg.constants.tb import AnalysisType
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase, MultiqcDataJson
from cg.models.raredisease.raredisease import (
    RarediseaseParameters,
    RarediseaseQCMetrics,
    RarediseaseSampleSheetEntry,
    RarediseaseSampleSheetHeaders,
)
from cg.resources import RAREDISEASE_BUNDLE_FILENAMES_PATH
from cg.store.models import CaseSample, Sample

LOG = logging.getLogger(__name__)


class RarediseaseAnalysisAPI(NfAnalysisAPI):
    """Handles communication between RAREDISEASE processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.RAREDISEASE,
    ):
        super().__init__(config=config, workflow=workflow)
        self.root_dir: str = config.raredisease.root
        self.workflow_bin_path: str = config.raredisease.workflow_bin_path
        self.profile: str = config.raredisease.profile
        self.conda_env: str = config.raredisease.conda_env
        self.conda_binary: str = config.raredisease.conda_binary
        self.platform: str = config.raredisease.platform
        self.params: str = config.raredisease.params
        self.workflow_config_path: str = config.raredisease.config
        self.resources: str = config.raredisease.resources
        self.tower_binary_path: str = config.tower_binary_path
        self.tower_workflow: str = config.raredisease.tower_workflow
        self.account: str = config.raredisease.slurm.account
        self.email: str = config.raredisease.slurm.mail_user
        self.compute_env_base: str = config.raredisease.compute_env
        self.revision: str = config.raredisease.revision
        self.nextflow_binary_path: str = config.raredisease.binary_path

    @property
    def sample_sheet_headers(self) -> list[str]:
        """Headers for sample sheet."""
        return RarediseaseSampleSheetHeaders.list()

    def get_sample_sheet_content_per_sample(self, case_sample: CaseSample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        fastq_forward_read_paths, fastq_reverse_read_paths = self.get_paired_read_paths(
            sample=case_sample.sample
        )
        sample_sheet_entry = RarediseaseSampleSheetEntry(
            name=case_sample.sample.internal_id,
            fastq_forward_read_paths=fastq_forward_read_paths,
            fastq_reverse_read_paths=fastq_reverse_read_paths,
            sex=self.get_sex_code(case_sample.sample.sex),
            phenotype=self.get_phenotype_code(case_sample.status),
            paternal_id=case_sample.get_paternal_sample_id,
            maternal_id=case_sample.get_maternal_sample_id,
            case_id=case_sample.case.internal_id,
        )
        return sample_sheet_entry.reformat_sample_content

    @property
    def is_gene_panel_required(self) -> bool:
        """Return True if a gene panel needs to be created using the information in StatusDB and exporting it from Scout."""
        return True

    def get_built_workflow_parameters(
        self, case_id: str, dry_run: bool = False
    ) -> RarediseaseParameters:
        """Return parameters."""
        analysis_type: AnalysisType = self.get_data_analysis_type(case_id=case_id)
        target_bed_file: str = self.get_target_bed_from_lims(case_id=case_id) or ""
        outdir = self.get_case_path(case_id=case_id)
        sample_id_map: Path = self.get_sample_name_mapping_csv_path(case=case_id)
        # Build the sample_id_map path
        if not dry_run:
            self.export_customer_internal_mapping_csv(case=case_id, output_path=sample_id_map)

        return RarediseaseParameters(
            input=self.get_sample_sheet_path(case_id=case_id),
            outdir=outdir,
            analysis_type=analysis_type,
            target_bed_file=target_bed_file,
            save_mapped_as_cram=True,
            vcfanno_extra_resources=f"{outdir}/{ScoutExportFileName.MANAGED_VARIANTS}",
            vep_filters_scout_fmt=f"{outdir}/{ScoutExportFileName.PANELS}",
            sample_id_map=sample_id_map,
        )

    @staticmethod
    def get_phenotype_code(phenotype: str) -> int:
        """Return Raredisease phenotype code."""
        LOG.debug("Translate phenotype to integer code")
        try:
            code = PlinkPhenotypeStatus[phenotype.upper()]
        except KeyError:
            raise ValueError(f"{phenotype} is not a valid phenotype")
        return code

    @staticmethod
    def get_sex_code(sex: str) -> int:
        """Return Raredisease sex code."""
        LOG.debug("Translate sex to integer code")
        try:
            code = PlinkSex[sex.upper()]
        except KeyError:
            raise ValueError(f"{sex} is not a valid sex")
        return code

    @staticmethod
    def get_bundle_filenames_path() -> Path:
        """Return Raredisease bundle filenames path."""
        return RAREDISEASE_BUNDLE_FILENAMES_PATH

    @property
    def is_managed_variants_required(self) -> bool:
        """Return True if a managed variants needs to be exported from Scout."""
        return True

    def write_managed_variants(self, case_id: str, content: list[str]) -> None:
        self._write_managed_variants(out_dir=Path(self.root, case_id), content=content)

    def get_managed_variants(self, case_id: str) -> list[str]:
        """Create and return the managed variants."""
        return self._get_managed_variants(
            genome_build=self.get_gene_panel_genome_build(case_id=case_id)
        )

    def get_workflow_metrics(self, sample_id: str) -> dict:
        """Return Raredisease workflow metric conditions for a sample."""
        sample: Sample = self.status_db.get_sample_by_internal_id(internal_id=sample_id)
        if "-" not in sample_id:
            metric_conditions: dict[str, dict[str, Any]] = (
                self.get_metric_conditions_by_prep_category(sample_id=sample.internal_id)
            )
            self.set_order_sex_for_sample(sample=sample, metric_conditions=metric_conditions)
        else:
            metric_conditions = RAREDISEASE_PARENT_PEDDY_METRIC_CONDITION.copy()
        return metric_conditions

    def get_metric_conditions_by_prep_category(self, sample_id: str) -> dict:
        sample: Sample = self.status_db.get_sample_by_internal_id(internal_id=sample_id)
        if (
            sample.application_version.application.analysis_type
            == SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
        ):
            return RAREDISEASE_METRIC_CONDITIONS_WGS.copy()
        return RAREDISEASE_METRIC_CONDITIONS_WES.copy()

    def _get_sample_pair_patterns(self, case_id: str) -> list[str]:
        """Return sample-pair patterns for searching in MultiQC."""
        sample_ids: list[str] = list(self.status_db.get_sample_ids_by_case_id(case_id=case_id))
        pairwise_patterns: list[str] = [
            f"{sample1}-{sample2}" for sample1, sample2 in permutations(sample_ids, 2)
        ]
        return pairwise_patterns

    def get_parent_error_ped_check_metric(
        self, pair_sample_ids: str, multiqc_raw_data: dict[dict]
    ) -> MetricsBase | None:
        """Return the parsed metrics for pedigree error given a concatenated pair of sample ids."""
        metric_name: str = "parent_error_ped_check"
        peddy_metrics: dict[str, dict] = multiqc_raw_data["multiqc_peddy"]
        if sample_pair_metrics := peddy_metrics.get(pair_sample_ids, None):
            return self.get_multiqc_metric(
                metric_name=metric_name,
                metric_value=sample_pair_metrics[metric_name],
                metric_id=pair_sample_ids,
            )

    def get_raredisease_multiqc_json_metrics(self, case_id: str) -> list[MetricsBase]:
        """Return a list of the metrics specified in a MultiQC json file."""
        multiqc_json: MultiqcDataJson = self.get_multiqc_data_json(case_id=case_id)
        metrics = []
        for search_pattern, metric_id in self.get_multiqc_search_patterns(case_id).items():
            metrics_for_pattern: list[MetricsBase] = (
                self.get_metrics_from_multiqc_json_with_pattern(
                    search_pattern=search_pattern,
                    multiqc_json=multiqc_json,
                    metric_id=metric_id,
                    exact_match=self.is_multiqc_pattern_search_exact,
                )
            )
            metrics.extend(metrics_for_pattern)
        for sample_pair in self._get_sample_pair_patterns(case_id):
            if parent_error_metric := self.get_parent_error_ped_check_metric(
                pair_sample_ids=sample_pair, multiqc_raw_data=multiqc_json.report_saved_raw_data
            ):
                metrics.append(parent_error_metric)
        metrics = self.get_deduplicated_metrics(metrics=metrics)
        return metrics

    def create_metrics_deliverables_content(self, case_id: str) -> dict[str, list[dict[str, Any]]]:
        """Create the content of a Raredisease metrics deliverables file."""
        metrics: list[MetricsBase] = self.get_raredisease_multiqc_json_metrics(case_id=case_id)
        self.ensure_mandatory_metrics_present(metrics=metrics)
        return {"metrics": [metric.dict() for metric in metrics]}

    @staticmethod
    def set_order_sex_for_sample(sample: Sample, metric_conditions: dict) -> None:
        metric_conditions["predicted_sex_sex_check"]["threshold"] = sample.sex
        metric_conditions["gender"]["threshold"] = sample.sex

    def get_sample_coverage_file_path(self, bundle_name: str, sample_id: str) -> str | None:
        """Return the Raredisease d4 coverage file path."""
        coverage_file_tags: list[str] = RAREDISEASE_COVERAGE_FILE_TAGS + [sample_id]
        coverage_file: File | None = self.housekeeper_api.get_file_from_latest_version(
            bundle_name=bundle_name, tags=coverage_file_tags
        )
        if coverage_file:
            return coverage_file.full_path
        LOG.warning(f"No coverage file found with the tags: {coverage_file_tags}")
        return None

    def get_sample_coverage(
        self, case_id: str, sample_id: str, gene_ids: list[int]
    ) -> CoverageMetrics | None:
        """Return sample coverage metrics from Chanjo2."""
        genome_version: GenomeVersion = self.get_genome_build(case_id)
        coverage_file_path: str | None = self.get_sample_coverage_file_path(
            bundle_name=case_id, sample_id=sample_id
        )
        try:
            post_request = CoveragePostRequest(
                build=self.translate_genome_reference(genome_version),
                coverage_threshold=RAREDISEASE_COVERAGE_THRESHOLD,
                hgnc_gene_ids=gene_ids,
                interval_type=RAREDISEASE_COVERAGE_INTERVAL_TYPE,
                samples=[CoverageSample(coverage_file_path=coverage_file_path, name=sample_id)],
            )
            post_response: CoveragePostResponse = self.chanjo2_api.get_coverage(post_request)
            return post_response.get_sample_coverage_metrics(sample_id)
        except Exception as error:
            LOG.error(f"Error getting coverage for sample '{sample_id}', error: {error}")
            return None

    def get_scout_upload_case_tags(self) -> dict:
        """Return Raredisease Scout upload case tags."""
        return RAREDISEASE_CASE_TAGS

    def get_genome_build(self, case_id: str) -> GenomeVersion:
        """Return reference genome for a raredisease case. Currently fixed for hg19."""
        return GenomeVersion.HG19

    def parse_analysis(self, qc_metrics_raw: list[MetricsBase], **kwargs) -> NextflowAnalysis:
        """Parse Nextflow output analysis files and return an analysis model."""
        qc_metrics_model = RarediseaseQCMetrics
        return super().parse_analysis(
            qc_metrics_raw=qc_metrics_raw, qc_metrics_model=qc_metrics_model, **kwargs
        )

    def get_sample_name_mapping_csv_path(self, case: str) -> Path:
        """Return the path to the CSV file containing the mapping between sample names and internal ids."""
        return Path(self.get_case_path(case), f"{case}_customer_internal_mapping.csv")

    def export_customer_internal_mapping_csv(self, case: str, output_path: Path):
        """Export a CSV file mapping customer sample names to internal sample IDs."""
        LOG.info(f"Exporting customer internal mapping CSV for case {case} to {output_path}")
        with output_path.open("w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                ["customer_id", "internal_id"]
            )  # this is the header expected by the pipeline
            for link in self.status_db.get_case_by_internal_id(case).links:
                customer_sample_name = link.sample.name
                internal_id = link.sample.internal_id
                writer.writerow([customer_sample_name, internal_id])
