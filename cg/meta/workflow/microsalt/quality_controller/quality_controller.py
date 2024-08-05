import logging
from pathlib import Path

from cg.meta.workflow.microsalt.constants import QUALITY_REPORT_FILE_NAME
from cg.meta.workflow.microsalt.metrics_parser import (
    MetricsParser,
    QualityMetrics,
    SampleMetrics,
)
from cg.meta.workflow.microsalt.quality_controller.models import (
    CaseQualityResult,
    QualityResult,
    SampleQualityResult,
)
from cg.meta.workflow.microsalt.quality_controller.report_generator import (
    ReportGenerator,
)
from cg.meta.workflow.microsalt.quality_controller.result_logger import ResultLogger
from cg.meta.workflow.microsalt.quality_controller.utils import (
    get_application_tag,
    get_percent_reads_guaranteed,
    get_report_path,
    get_sample_target_reads,
    has_non_microbial_apptag,
    has_valid_10x_coverage,
    has_valid_average_coverage,
    has_valid_duplication_rate,
    has_valid_mapping_rate,
    has_valid_median_insert_size,
    is_sample_negative_control,
    is_valid_total_reads,
    is_valid_total_reads_for_negative_control,
    quality_control_case,
)
from cg.store.models import Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class MicroSALTQualityController:
    def __init__(self, status_db: Store):
        self.status_db = status_db

    def quality_control(self, case_metrics_file_path: Path) -> QualityResult:
        quality_metrics: QualityMetrics = MetricsParser.parse(case_metrics_file_path)
        sample_results: list[SampleQualityResult] = self.quality_control_samples(quality_metrics)
        case_result: CaseQualityResult = quality_control_case(sample_results)
        report_file: Path = get_report_path(case_metrics_file_path)
        ReportGenerator.report(out_file=report_file, samples=sample_results, case=case_result)
        ResultLogger.log_results(case=case_result, samples=sample_results, report=report_file)
        summary: str = ReportGenerator.get_summary(
            case=case_result, samples=sample_results, report_path=report_file
        )
        return QualityResult(case=case_result, samples=sample_results, summary=summary)

    def quality_control_samples(self, quality_metrics: QualityMetrics) -> list[SampleQualityResult]:
        sample_results: list[SampleQualityResult] = []
        for sample_id, metrics in quality_metrics.samples.items():
            result = self.quality_control_sample(sample_id=sample_id, metrics=metrics)
            sample_results.append(result)
        return sample_results

    def quality_control_sample(self, sample_id: str, metrics: SampleMetrics) -> SampleQualityResult:
        """Perform a quality control of a sample given its metrics."""
        valid_read_count: bool = self.has_valid_total_reads(sample_id)
        valid_mapping: bool = has_valid_mapping_rate(metrics)
        valid_duplication: bool = has_valid_duplication_rate(metrics)
        valid_inserts: bool = has_valid_median_insert_size(metrics)
        valid_coverage: bool = has_valid_average_coverage(metrics)
        valid_10x_coverage: bool = has_valid_10x_coverage(metrics)

        sample: Sample = self.status_db.get_sample_by_internal_id(sample_id)
        application_tag: str = get_application_tag(sample)

        if is_control := is_sample_negative_control(sample):
            sample_quality = SampleQualityResult(
                sample_id=sample_id,
                passes_qc=valid_read_count,
                is_control=is_control,
                passes_reads_qc=valid_read_count,
                application_tag=application_tag,
            )
            ResultLogger.log_sample_result(sample_quality)
            return sample_quality

        sample_passes_qc: bool = (
            valid_read_count
            and valid_mapping
            and valid_duplication
            and valid_inserts
            and valid_coverage
            and valid_10x_coverage
        )

        if has_non_microbial_apptag(sample):
            sample_passes_qc = valid_read_count

        sample_quality = SampleQualityResult(
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
        ResultLogger.log_sample_result(sample_quality)
        return sample_quality

    def is_qc_required(self, case_run_dir: Path) -> bool:
        if not case_run_dir:
            LOG.warning(f"Skipping QC, run directory {case_run_dir} does not exist.")
            return False
        qc_done_path: Path = case_run_dir.joinpath(QUALITY_REPORT_FILE_NAME)
        qc_already_done: bool = qc_done_path.exists()
        if qc_already_done:
            LOG.warning(f"Skipping QC, report {qc_done_path} already exists.")
        return not qc_done_path.exists()

    def has_valid_total_reads(self, sample_id: str) -> bool:
        sample: Sample = self.status_db.get_sample_by_internal_id(sample_id)
        target_reads: int = get_sample_target_reads(sample)
        percent_reads_guaranteed: int = get_percent_reads_guaranteed(sample)
        sample_reads: int = sample.reads

        if is_sample_negative_control(sample):
            return is_valid_total_reads_for_negative_control(
                reads=sample_reads, target_reads=target_reads
            )

        return is_valid_total_reads(
            reads=sample_reads,
            target_reads=target_reads,
            threshold_percentage=percent_reads_guaranteed,
        )
