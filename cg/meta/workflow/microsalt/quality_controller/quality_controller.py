import logging
from pathlib import Path

from cg.io.json import write_json
from cg.meta.workflow.microsalt.metrics_parser import MetricsParser
from cg.meta.workflow.microsalt.metrics_parser.models import QualityMetrics, SampleMetrics
from cg.meta.workflow.microsalt.quality_controller.models import QualityResult
from cg.meta.workflow.microsalt.quality_controller.report_generatory import ReportGenerator
from cg.meta.workflow.microsalt.quality_controller.utils import (
    get_application_tag,
    is_sample_negative_control,
    is_valid_10x_coverage,
    is_valid_average_coverage,
    is_valid_duplication_rate,
    is_valid_mapping_rate,
    is_valid_median_insert_size,
    is_valid_negative_control,
    is_valid_total_reads,
    is_valid_total_reads_for_control,
    non_urgent_samples_pass_qc,
    urgent_samples_pass_qc,
)
from cg.models.orders.sample_base import ControlEnum
from cg.store.api.core import Store
from cg.store.models import Sample

LOG = logging.getLogger(__name__)


class QualityController:
    def __init__(self, status_db: Store):
        self.status_db = status_db

    def quality_control(self, metrics_file_path: Path) -> bool:
        quality_metrics: QualityMetrics = MetricsParser.parse(metrics_file_path)
        sample_results: list[QualityResult] = []

        for sample_id, metrics in quality_metrics:
            result = self.quality_control_sample(sample_id=sample_id, metrics=metrics)
            sample_results.append(result)

        ReportGenerator.report(out_dir=metrics_file_path.parent, results=sample_results)
        return self.quality_control_case(sample_results)

    def quality_control_sample(self, sample_id: str, metrics: SampleMetrics) -> QualityResult:
        valid_reads: bool = self.is_valid_total_reads(sample_id)
        valid_mapping: bool = is_valid_mapping_rate(metrics)
        valid_duplication: bool = is_valid_duplication_rate(metrics)
        valid_inserts: bool = is_valid_median_insert_size(metrics)
        valid_coverage: bool = is_valid_average_coverage(metrics)
        valid_10x_coverage: bool = is_valid_10x_coverage(metrics)

        sample_passes_qc: bool = (
            valid_reads
            and valid_mapping
            and valid_duplication
            and valid_inserts
            and valid_coverage
            and valid_10x_coverage
        )

        sample: Sample = self.status_db.get_sample_by_internal_id(sample_id)
        is_control: bool = is_sample_negative_control(sample)
        application_tag: str = get_application_tag(sample)

        return QualityResult(
            sample_id=sample_id,
            passed=sample_passes_qc,
            is_control=is_control,
            application_tag=application_tag,
            passes_reads_qc=valid_reads,
            passes_mapping_qc=valid_mapping,
            passes_duplication_qc=valid_duplication,
            passes_inserts_qc=valid_inserts,
            passes_coverage_qc=valid_coverage,
            passes_10x_coverage_qc=valid_10x_coverage,
        )

    def quality_control_case(self, sample_results: list[QualityResult]) -> bool:
        control_passes_qc: bool = is_valid_negative_control(sample_results)
        urgent_pass_qc: bool = urgent_samples_pass_qc(sample_results)
        non_urgent_pass_qc: bool = non_urgent_samples_pass_qc(sample_results)
        return control_passes_qc and urgent_pass_qc and non_urgent_pass_qc

    def is_qc_required(self, case_run_dir: Path) -> bool:
        if case_run_dir is None:
            return False
        qc_done_path: Path = case_run_dir.joinpath("QC_done.json")
        return not qc_done_path.exists()

    def is_valid_total_reads(self, sample_id: str) -> bool:
        sample: Sample = self.status_db.get_sample_by_internal_id(sample_id)
        target_reads: int = sample.application_version.application.target_reads
        sample_reads: int = sample.reads

        if sample.control == ControlEnum.negative:
            return is_valid_total_reads_for_control(reads=sample_reads, target_reads=target_reads)
        return is_valid_total_reads(reads=sample_reads, target_reads=target_reads)
