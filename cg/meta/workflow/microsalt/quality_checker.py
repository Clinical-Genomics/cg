import logging
from pathlib import Path

from cg.io.json import write_json
from cg.constants.constants import MicrosaltQC
from cg.meta.workflow.microsalt.models import QualityMetrics, QualityResult, SampleMetrics
from cg.meta.workflow.microsalt.utils import (
    get_application_tag,
    get_negative_control_result,
    get_non_urgent_results,
    get_results_passing_qc,
    get_urgent_results,
    is_sample_negative_control,
    is_valid_10x_coverage,
    is_valid_average_coverage,
    is_valid_duplication_rate,
    is_valid_mapping_rate,
    is_valid_median_insert_size,
    is_valid_total_reads,
    is_valid_total_reads_for_control,
    parse_quality_metrics,
)
from cg.models.orders.sample_base import ControlEnum
from cg.store.api.core import Store
from cg.store.models import Sample

LOG = logging.getLogger(__name__)


class QualityChecker:
    def __init__(self, status_db: Store):
        self.status_db = status_db

    def microsalt_qc(self, metrics_file_path: Path) -> bool:
        quality_metrics: QualityMetrics = parse_quality_metrics(metrics_file_path)
        sample_results: list[QualityResult] = []

        for sample_id, metrics in quality_metrics:
            result = self.quality_control_sample(sample_id=sample_id, metrics=metrics)
            sample_results.append(result)

        return self.quality_control_case(sample_results)

    def quality_control_sample(self, sample_id: str, metrics: SampleMetrics) -> QualityResult:
        valid_reads: bool = self.is_valid_total_reads(sample_id)
        valid_mapping: bool = self.is_valid_mapped_rate(metrics)
        valid_duplication: bool = self.is_valid_duplication_rate(metrics)
        valid_inserts: bool = self.is_valid_median_insert_size(metrics)
        valid_coverage: bool = self.is_valid_average_coverage(metrics)
        valid_10x_coverage: bool = self.is_valid_10x_coverage(metrics)

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
            is_negative_control=is_control,
            application_tag=application_tag,
        )

    def quality_control_case(self, sample_results: list[QualityResult]) -> bool:
        control_passes_qc: bool = self.is_valid_negative_control(sample_results)
        urgent_pass_qc: bool = self.all_urgent_samples_pass_qc(sample_results)
        non_urgent_pass_qc: bool = self.non_urgent_samples_pass_qc(sample_results)
        return control_passes_qc and urgent_pass_qc and non_urgent_pass_qc

    def is_qc_required(self, case_run_dir: Path | None, case_id: str) -> bool:
        """Checks if a qc is required for a microbial case."""
        if case_run_dir is None:
            LOG.info(f"There are no running directories for case {case_id}.")
            return False

        if case_run_dir.joinpath("QC_done.json").exists():
            LOG.info(f"QC already performed for case {case_id}, storing case.")
            return False

        LOG.info(f"Performing QC on case {case_id}")
        return True

    def create_qc_done_file(self, run_dir_path: Path, failed_samples: dict) -> None:
        """Creates a QC_done when a QC check is performed."""
        write_json(file_path=run_dir_path.joinpath("QC_done.json"), content=failed_samples)

    def is_valid_total_reads(self, sample_id: str) -> bool:
        sample: Sample = self.status_db.get_sample_by_internal_id(sample_id)
        target_reads: int = sample.application_version.application.target_reads
        sample_reads: int = sample.reads

        if sample.control == ControlEnum.negative:
            return is_valid_total_reads_for_control(reads=sample_reads, target_reads=target_reads)
        return is_valid_total_reads(reads=sample_reads, target_reads=target_reads)

    def is_valid_mapped_rate(self, metrics: SampleMetrics) -> bool:
        mapped_rate: float | None = metrics.microsalt_samtools_stats.mapped_rate
        return is_valid_mapping_rate(mapped_rate) if mapped_rate else False

    def is_valid_duplication_rate(self, metrics: SampleMetrics) -> bool:
        duplication_rate: float | None = metrics.picard_markduplicate.duplication_rate
        return is_valid_duplication_rate(duplication_rate) if duplication_rate else False

    def is_valid_median_insert_size(self, metrics: SampleMetrics) -> bool:
        insert_size: int | None = metrics.picard_markduplicate.insert_size
        return is_valid_median_insert_size(insert_size) if insert_size else False

    def is_valid_average_coverage(self, metrics: SampleMetrics) -> bool:
        coverage: float | None = metrics.microsalt_samtools_stats.average_coverage
        return is_valid_average_coverage(coverage) if coverage else False

    def is_valid_10x_coverage(self, metrics: SampleMetrics) -> bool:
        coverage_10x: float | None = metrics.microsalt_samtools_stats.coverage_10x
        return is_valid_10x_coverage(coverage_10x) if coverage_10x else False

    def is_valid_negative_control(self, results: list[QualityResult]) -> bool:
        negative_control_result: QualityResult = get_negative_control_result(results)
        return negative_control_result.passes_qc

    def all_urgent_samples_pass_qc(self, results: list[QualityResult]) -> bool:
        urgent_samples: list[QualityResult] = get_urgent_results(results)
        return all(sample.passes_qc for sample in urgent_samples)

    def non_urgent_samples_pass_qc(self, results: list[QualityResult]) -> bool:
        urgent_samples: list[QualityResult] = get_non_urgent_results(results)
        passing_qc: list[QualityResult] = get_results_passing_qc(urgent_samples)

        if not urgent_samples:
            return True

        fraction_passing_qc: float = len(passing_qc) / len(urgent_samples)
        return fraction_passing_qc >= MicrosaltQC.QC_PERCENT_THRESHOLD_MWX
