"""Module for Raredisease Analysis API."""

import copy
import logging
from itertools import permutations
from pathlib import Path
from typing import Any

from cg.apps.coverage import ChanjoAPI, chanjo_api_for_genome_build
from cg.constants import Workflow
from cg.constants.constants import WORKFLOW_TO_GENOME_VERSION_MAP, GenomeVersion
from cg.constants.nf_analysis import (
    RAREDISEASE_METRIC_CONDITIONS_WES,
    RAREDISEASE_METRIC_CONDITIONS_WGS,
    RAREDISEASE_PARENT_PEDDY_METRIC_CONDITION,
)
from cg.constants.scout import RAREDISEASE_CASE_TAGS
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.meta.workflow.utils.chanjo1 import CoverageMetricsChanjo1, chanjo1_get_sample_coverage
from cg.models.analysis import NextflowAnalysis
from cg.models.cg_config import CGConfig
from cg.models.deliverables.metric_deliverables import MetricsBase, MultiqcDataJson
from cg.models.raredisease.raredisease import RarediseaseQCMetrics
from cg.resources import RAREDISEASE_BUNDLE_FILENAMES_PATH
from cg.store.models import Sample

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
        self.chanjo_api: ChanjoAPI = chanjo_api_for_genome_build(
            config=config, genome_build=WORKFLOW_TO_GENOME_VERSION_MAP[Workflow.RAREDISEASE]
        )
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
        self.revision: str = config.raredisease.revision

    @staticmethod
    def get_bundle_filenames_path() -> Path:
        """Return Raredisease bundle filenames path."""
        return RAREDISEASE_BUNDLE_FILENAMES_PATH

    def get_qc_conditions_for_workflow(self, sample_id: str) -> dict:
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
                sample_id=pair_sample_ids,
            )

    def get_raredisease_multiqc_json_metrics(self, case_id: str) -> list[MetricsBase]:
        """Return a list of the metrics specified in a MultiQC json file."""
        multiqc_json: MultiqcDataJson = self.get_multiqc_data_json(case_id=case_id)
        metrics = []
        for pattern in self.get_multiqc_search_patterns(case_id=case_id):
            metrics_for_pattern: list[MetricsBase] = self.get_multiqc_metrics_for_sample(
                search_pattern=pattern.pattern,
                multiqc_json=multiqc_json,
                sample_id=pattern.sample_id,
                exact_match=self.is_multiqc_pattern_search_exact,
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

    def _get_list_of_metric_dicts(self, multiqc_json: MultiqcDataJson):
        metric_dicts: list[dict[str, Any]] = super()._get_list_of_metric_dicts(multiqc_json)
        list_copy: list[dict[str, Any]] = copy.deepcopy(metric_dicts)
        list_copy.append(self._get_multiqc_picard_dict(multiqc_json))

        return list_copy

    @staticmethod
    def _get_multiqc_picard_dict(multiqc_json: MultiqcDataJson) -> dict:
        """Return the Picard Align Summary metrics from a MultiQC json file as a dictionary."""
        picard_raw = copy.deepcopy(
            multiqc_json.report_saved_raw_data["multiqc_picard_AlignmentSummaryMetrics"]
        )
        for sample_id, metrics in picard_raw.items():
            picard_raw[sample_id] = {f"picard_{k}": v for k, v in metrics.items()}

        return picard_raw

    @staticmethod
    def set_order_sex_for_sample(sample: Sample, metric_conditions: dict) -> None:
        metric_conditions["predicted_sex_sex_check"]["threshold"] = sample.sex
        metric_conditions["gender"]["threshold"] = sample.sex

    def get_sample_coverage(
        self, case_id: str, sample_id: str, gene_ids: list[int]
    ) -> CoverageMetricsChanjo1 | None:
        return chanjo1_get_sample_coverage(
            chanjo_api=self.chanjo_api, sample_id=sample_id, gene_ids=gene_ids
        )

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
