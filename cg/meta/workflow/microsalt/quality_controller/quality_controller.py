import logging
from pathlib import Path
from cg.meta.workflow.microsalt.constants import QUALITY_REPORT_FILE_NAME

from cg.meta.workflow.microsalt.metrics_parser import MetricsParser, QualityMetrics, SampleMetrics
from cg.meta.workflow.microsalt.quality_controller.models import CaseQualityResult, QualityResult
from cg.meta.workflow.microsalt.quality_controller.report_generator import ReportGenerator
from cg.meta.workflow.microsalt.quality_controller.result_logger import ResultLogger
from cg.meta.workflow.microsalt.quality_controller.utils import (
    get_application_tag,
    get_sample_target_reads,
    is_sample_negative_control,
    has_valid_10x_coverage,
    has_valid_average_coverage,
    has_valid_duplication_rate,
    has_valid_mapping_rate,
    has_valid_median_insert_size,
    negative_control_pass_qc,
    is_valid_total_reads,
    is_valid_total_reads_for_negative_control,
    non_urgent_samples_pass_qc,
    urgent_samples_pass_qc,
)
from cg.store.api.core import Store
from cg.store.models import Sample

LOG = logging.getLogger(__name__)


class QualityController:
    def __init__(self, status_db: Store):
        self.status_db = status_db

    def quality_control(self, metrics_file_path: Path) -> bool:
        quality_metrics: QualityMetrics = MetricsParser.parse(metrics_file_path)
        sample_results: list[QualityResult] = self.quality_control_samples(quality_metrics)
        case_result: CaseQualityResult = self.quality_control_case(sample_results)
        report_file: Path = metrics_file_path.parent.joinpath(QUALITY_REPORT_FILE_NAME)
        ReportGenerator.report(out_file=report_file, sample_results=sample_results)
        ResultLogger.log_results(sample_results=sample_results, case_result=case_result)
        return case_result.passes_qc

    def quality_control_samples(self, quality_metrics: QualityMetrics) -> list[QualityResult]:
        sample_results: list[QualityResult] = []
        for sample_id, metrics in quality_metrics.samples.items():
            result = self.quality_control_sample(sample_id=sample_id, metrics=metrics)
            sample_results.append(result)
        return sample_results

    def quality_control_sample(self, sample_id: str, metrics: SampleMetrics) -> QualityResult:
        valid_read_count: bool = self.has_valid_total_reads(sample_id)
        valid_mapping: bool = has_valid_mapping_rate(metrics)
        valid_duplication: bool = has_valid_duplication_rate(metrics)
        valid_inserts: bool = has_valid_median_insert_size(metrics)
        valid_coverage: bool = has_valid_average_coverage(metrics)
        valid_10x_coverage: bool = has_valid_10x_coverage(metrics)

        sample_passes_qc: bool = (
            valid_read_count
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
            passes_qc=sample_passes_qc,
            is_control=is_control,
            application_tag=application_tag,
            passes_reads_qc=valid_read_count,
            passes_mapping_qc=valid_mapping,
            passes_duplication_qc=valid_duplication,
            passes_inserts_qc=valid_inserts,
            passes_coverage_qc=valid_coverage,
            passes_10x_coverage_qc=valid_10x_coverage,
        )

    def quality_control_case(self, sample_results: list[QualityResult]) -> CaseQualityResult:
        control_pass_qc: bool = negative_control_pass_qc(sample_results)
        urgent_pass_qc: bool = urgent_samples_pass_qc(sample_results)
        non_urgent_pass_qc: bool = non_urgent_samples_pass_qc(sample_results)

        case_passes_qc: bool = control_pass_qc and urgent_pass_qc and non_urgent_pass_qc

        return CaseQualityResult(
            passes_qc=case_passes_qc,
            control_passes_qc=control_pass_qc,
            urgent_passes_qc=urgent_pass_qc,
            non_urgent_passes_qc=non_urgent_pass_qc,
        )

    def is_qc_required(self, case_run_dir: Path) -> bool:
        if not case_run_dir:
            return False
        qc_done_path: Path = case_run_dir.joinpath(QUALITY_REPORT_FILE_NAME)
        return not qc_done_path.exists()

    def has_valid_total_reads(self, sample_id: str) -> bool:
        sample: Sample = self.status_db.get_sample_by_internal_id(sample_id)
        target_reads: int = get_sample_target_reads(sample)
        sample_reads: int = sample.reads

        if is_sample_negative_control(sample):
            return is_valid_total_reads_for_negative_control(reads=sample_reads, target_reads=target_reads)
        return is_valid_total_reads(reads=sample_reads, target_reads=target_reads)
