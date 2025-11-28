"""Module for Nallo Analysis API."""

import logging
from itertools import permutations
from pathlib import Path
from typing import Any

from click import File

from cg.clients.chanjo2.models import (
    CoverageMetrics,
    CoveragePostRequest,
    CoveragePostResponse,
    CoverageSample,
)
from cg.constants import Workflow
from cg.constants.constants import FileFormat, GenomeVersion
from cg.constants.nf_analysis import (
    NALLO_COVERAGE_FILE_TAGS,
    NALLO_COVERAGE_INTERVAL_TYPE,
    NALLO_COVERAGE_THRESHOLD,
    NALLO_GENERAL_METRIC_CONDITIONS,
    NALLO_PARENT_PEDDY_METRIC_CONDITION,
    NALLO_RAW_METRIC_CONDITIONS,
)
from cg.constants.scout import NALLO_CASE_TAGS, ScoutExportFileName
from cg.constants.subject import PlinkPhenotypeStatus, PlinkSex
from cg.io.controller import WriteFile
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase, MultiqcDataJson
from cg.models.nallo.nallo import (
    NalloParameters,
    NalloQCMetrics,
    NalloSampleSheetEntry,
    NalloSampleSheetHeaders,
)
from cg.resources import NALLO_BUNDLE_FILENAMES_PATH
from cg.store.models import CaseSample, Sample

LOG = logging.getLogger(__name__)


class NalloAnalysisAPI(NfAnalysisAPI):
    """Handles communication between Nallo processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.NALLO,
    ):
        super().__init__(config=config, workflow=workflow)
        self.root_dir: str = config.nallo.root
        self.workflow_bin_path: str = config.nallo.workflow_bin_path
        self.profile: str = config.nallo.profile
        self.conda_env: str = config.nallo.conda_env
        self.conda_binary: str = config.nallo.conda_binary
        self.platform: str = config.nallo.platform
        self.params: str = config.nallo.params
        self.workflow_config_path: str = config.nallo.config
        self.resources: str = config.nallo.resources
        self.tower_binary_path: str = config.tower_binary_path
        self.tower_workflow: str = config.nallo.tower_workflow
        self.account: str = config.nallo.slurm.account
        self.email: str = config.nallo.slurm.mail_user
        self.compute_env_base: str = config.nallo.compute_env
        self.revision: str = config.nallo.revision
        self.nextflow_binary_path: str = config.nallo.binary_path

    @property
    def sample_sheet_headers(self) -> list[str]:
        """Headers for sample sheet."""
        return NalloSampleSheetHeaders.list()

    def get_sample_sheet_content_per_sample(self, case_sample: CaseSample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        read_file_paths = self.get_bam_read_file_paths(sample=case_sample.sample)
        sample_sheet_entries = []

        for bam_path in read_file_paths:
            sample_sheet_entry = NalloSampleSheetEntry(
                project=case_sample.case.internal_id,
                sample=case_sample.sample.internal_id,
                read_file=Path(bam_path),
                family_id=case_sample.case.internal_id,
                paternal_id=case_sample.get_paternal_sample_id or "0",
                maternal_id=case_sample.get_maternal_sample_id or "0",
                sex=self.get_sex_code(case_sample.sample.sex),
                phenotype=self.get_phenotype_code(case_sample.status),
            )
            sample_sheet_entries.extend(sample_sheet_entry.reformat_sample_content)
        return sample_sheet_entries

    @staticmethod
    def get_phenotype_code(phenotype: str) -> int:
        """Return Nallo phenotype code."""
        LOG.debug("Translate phenotype to integer code")
        try:
            code = PlinkPhenotypeStatus[phenotype.upper()]
        except KeyError:
            raise ValueError(f"{phenotype} is not a valid phenotype")
        return code

    @staticmethod
    def get_sex_code(sex: str) -> int:
        """Return Nallo sex code."""
        LOG.debug("Translate sex to integer code")
        try:
            code = PlinkSex[sex.upper()]
        except KeyError:
            raise ValueError(f"{sex} is not a valid sex")
        return code

    def get_built_workflow_parameters(self, case_id: str, dry_run: bool = False) -> NalloParameters:
        """Return parameters."""
        outdir = self.get_case_path(case_id=case_id)

        return NalloParameters(
            input=self.get_sample_sheet_path(case_id=case_id),
            outdir=outdir,
            filter_variants_hgnc_ids=f"{outdir}/{ScoutExportFileName.PANELS_TSV}",
        )

    @property
    def is_gene_panel_required(self) -> bool:
        """Return True if a gene panel needs to be created using information in StatusDB and exporting it from Scout."""
        return True

    def create_gene_panel(self, case_id: str, dry_run: bool) -> None:
        """Create and write an aggregated gene panel file exported from Scout as tsv file."""
        LOG.info("Creating gene panel file")
        bed_lines: list[str] = self.get_gene_panel(case_id=case_id, dry_run=dry_run)
        if dry_run:
            bed_lines: str = "\n".join(bed_lines)
            LOG.debug(f"{bed_lines}")
            return
        self.write_panel_as_tsv(case_id=case_id, content=bed_lines)

    def write_panel_as_tsv(self, case_id: str, content: list[str]) -> None:
        """Write the gene panel to case dir."""
        self._write_panel_as_tsv(out_dir=Path(self.root, case_id), content=content)

    @staticmethod
    def _write_panel_as_tsv(out_dir: Path, content: list[str]) -> None:
        """Write the gene panel to case dir while omitted the commented BED lines."""
        filtered_content = [line for line in content if not line.startswith("##")]
        out_dir.mkdir(parents=True, exist_ok=True)
        WriteFile.write_file_from_content(
            content="\n".join(filtered_content),
            file_format=FileFormat.TXT,
            file_path=Path(out_dir, ScoutExportFileName.PANELS_TSV),
        )

    def get_genome_build(self, case_id: str) -> GenomeVersion:
        """Return reference genome for a Nallo case. Currently fixed for hg38."""
        return GenomeVersion.HG38

    @staticmethod
    def get_bundle_filenames_path() -> Path:
        """Return Nallo bundle filenames path."""
        return NALLO_BUNDLE_FILENAMES_PATH

    def get_workflow_metrics(self, sample_id: str) -> dict:
        """Return Nallo workflow metric conditions for a sample."""
        sample: Sample = self.status_db.get_sample_by_internal_id(internal_id=sample_id)
        if "-" not in sample_id:
            metric_conditions: dict[str, dict[str, Any]] = NALLO_GENERAL_METRIC_CONDITIONS.copy()
            metric_conditions.update(NALLO_RAW_METRIC_CONDITIONS)
            self.set_somalier_sex_for_sample(sample=sample, metric_conditions=metric_conditions)
        else:
            metric_conditions = NALLO_PARENT_PEDDY_METRIC_CONDITION.copy()
        return metric_conditions

    def _get_nallo_sample_pair_patterns(self, case_id: str) -> list[str]:
        """Return sample-pair patterns for searching in MultiQC."""
        sample_ids: list[str] = list(self.status_db.get_sample_ids_by_case_id(case_id=case_id))
        pairwise_patterns: list[str] = [
            f"{sample1}-{sample2}" for sample1, sample2 in permutations(sample_ids, 2)
        ]
        return pairwise_patterns

    def get_nallo_parent_error_ped_check_metric(
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

    def get_nallo_raw_metric(self, sample_id: str, multiqc_raw_data: dict) -> MetricsBase | None:
        metric_name = "sex"
        raw_metrics_section: dict[str, dict] = multiqc_raw_data.get("multiqc_somalier", {})
        sample_metrics = raw_metrics_section.get(sample_id)
        if sample_metrics and metric_name in sample_metrics:
            return self.get_multiqc_metric(
                metric_name="somalier_sex",
                metric_value=sample_metrics[metric_name],
                metric_id=sample_id,
            )

    def get_nallo_multiqc_json_metrics(self, case_id: str) -> list[MetricsBase]:
        """Return a list of the Nallo metrics specified in a MultiQC json file."""
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
        for sample_id in self.status_db.get_sample_ids_by_case_id(case_id):
            if raw_metric := self.get_nallo_raw_metric(
                sample_id=sample_id,
                multiqc_raw_data=multiqc_json.report_saved_raw_data,
            ):
                metrics.append(raw_metric)
        for sample_pair in self._get_nallo_sample_pair_patterns(case_id):
            if parent_error_metric := self.get_nallo_parent_error_ped_check_metric(
                pair_sample_ids=sample_pair, multiqc_raw_data=multiqc_json.report_saved_raw_data
            ):
                metrics.append(parent_error_metric)
        metrics = self.get_deduplicated_metrics(metrics=metrics)
        return metrics

    @staticmethod
    def set_somalier_sex_for_sample(sample: Sample, metric_conditions: dict) -> None:
        if "somalier_sex" in metric_conditions:
            metric_conditions["somalier_sex"]["threshold"] = float(
                {
                    "male": PlinkSex.MALE,
                    "female": PlinkSex.FEMALE,
                    "unknown": PlinkSex.UNKNOWN,
                }[sample.sex]
            )

    def get_sample_coverage_file_path(self, bundle_name: str, sample_id: str) -> str | None:
        """Return the Nallo d4 coverage file path."""
        nallo_coverage_file_tags: list[str] = NALLO_COVERAGE_FILE_TAGS + [sample_id]
        nallo_coverage_file: File | None = self.housekeeper_api.get_file_from_latest_version(
            bundle_name=bundle_name, tags=nallo_coverage_file_tags
        )
        if nallo_coverage_file:
            return nallo_coverage_file.full_path
        LOG.warning(f"No Nallo coverage file found with the tags: {nallo_coverage_file_tags}")
        return None

    def get_sample_coverage(
        self, case_id: str, sample_id: str, gene_ids: list[int]
    ) -> CoverageMetrics | None:
        """Return sample coverage metrics from Chanjo2."""
        nallo_genome_version: GenomeVersion = self.get_genome_build(case_id)
        nallo_coverage_file_path: str | None = self.get_sample_coverage_file_path(
            bundle_name=case_id, sample_id=sample_id
        )
        try:
            post_request = CoveragePostRequest(
                build=self.translate_genome_reference(nallo_genome_version),
                coverage_threshold=NALLO_COVERAGE_THRESHOLD,
                hgnc_gene_ids=gene_ids,
                interval_type=NALLO_COVERAGE_INTERVAL_TYPE,
                samples=[
                    CoverageSample(coverage_file_path=nallo_coverage_file_path, name=sample_id)
                ],
            )
            post_response: CoveragePostResponse = self.chanjo2_api.get_coverage(post_request)
            return post_response.get_sample_coverage_metrics(sample_id)
        except Exception as error:
            LOG.error(f"Error getting coverage for sample '{sample_id}', error: {error}")
            return None

    def get_scout_upload_case_tags(self) -> dict:
        """Return Nallo Scout upload case tags."""
        return NALLO_CASE_TAGS

    def parse_analysis(self, qc_metrics_raw: list[MetricsBase], **kwargs) -> NextflowAnalysis:
        """Parse Nextflow output analysis files and return an analysis model."""
        qc_metrics_model = NalloQCMetrics
        return super().parse_analysis(
            qc_metrics_raw=qc_metrics_raw, qc_metrics_model=qc_metrics_model, **kwargs
        )

    def create_metrics_deliverables_content(self, case_id: str) -> dict[str, list[dict[str, Any]]]:
        """Create the content of a Nallo metrics deliverables file."""
        metrics: list[MetricsBase] = self.get_nallo_multiqc_json_metrics(case_id=case_id)
        self.ensure_mandatory_metrics_present(metrics=metrics)
        return {"metrics": [metric.dict() for metric in metrics]}
