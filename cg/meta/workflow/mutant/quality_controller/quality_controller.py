from pathlib import Path
from cg.constants.constants import MutantQC
from cg.meta.workflow.mutant.metadata_parser.metadata_parser import MetadataParser
from cg.meta.workflow.mutant.metadata_parser.models import SamplesMetadataMetrics
from cg.meta.workflow.mutant.metrics_parser import MetricsParser, SampleMetrics
from cg.meta.workflow.mutant.metrics_parser.models import SampleResultsMetrics
from cg.meta.workflow.mutant.quality_controller.models import (
    QualityMetrics,
    SampleQualityResult,
    CaseQualityResult,
    QualityResult,
)

from cg.meta.workflow.mutant.quality_controller.result_logger import ResultLogger
from cg.meta.workflow.mutant.quality_controller.utils import (
    has_valid_total_reads,
    internal_negative_control_qc_pass,
    external_negative_control_qc_pass,
    get_quality_metrics,
    is_valid_total_reads,
    is_valid_total_reads_for_external_negative_control,
    is_valid_total_reads_for_internal_negative_control,
)
from cg.store.store import Store
from cg.store.models import Case


class QualityController:
    def __init__(self, status_db: Store):
        # self.status_db = status_db
        self.metadata_parser = MetadataParser(status_db)

    def quality_control(self, case_results_file_path: Path, case: Case) -> QualityResult:
        quality_metrics: QualityMetrics = get_quality_metrics(case_results_file_path, case)
        sample_results: list[SampleQualityResult] = self.quality_control_samples(quality_metrics)
        case_result: CaseQualityResult = self.quality_control_case(sample_results)
        return case_result

        # TODO
        # report_file: Path = get_report_path(case_metrics_file_path)
        # ReportGenerator.report(out_file=report_file, samples=sample_results, case=case_result)
        # ResultLogger.log_results(case=case_result, samples=sample_results, report=report_file)
        # summary: str = ReportGenerator.get_summary(
        #     case=case_result, samples=sample_results, report_path=report_file
        # )
        # return QualityResult(case=case_result, samples=sample_results, summary=summary)

    def quality_control_samples(self, quality_metrics: QualityMetrics) -> list[SampleQualityResult]:
        sample_results: list[SampleQualityResult] = []

        for sample_id in quality_metrics.sample_id_list:
            result = self.quality_control_sample(sample_id, quality_metrics)
            sample_results.append(result)

        return sample_results

    def quality_control_sample(
        self, sample_id: str, quality_metrics: QualityMetrics
    ) -> SampleQualityResult:
        sample_metadata = quality_metrics.samples_metadata[sample_id]
        sample_results = quality_metrics.samples_results[sample_id]

        valid_read_count: bool = has_valid_total_reads(sample_metadata)

        if sample_metadata.is_internal_negative_control:
            sample_quality = SampleQualityResult(
                sample_id=sample_id,
                passes_qc=valid_read_count,
                is_external_negative_control=sample_metadata.is_external_negative_control,
                is_internal_negative_control=sample_metadata.is_internal_negative_control,
                passes_reads_threshold=valid_read_count,
            )
            return sample_quality

        sample_passes_qc: bool = valid_read_count and sample_results.qc_pass

        sample_quality = SampleQualityResult(
            sample_id=sample_id,
            passes_qc=sample_passes_qc,
            is_external_negative_control=sample_metadata.is_external_negative_control,
            is_internal_negative_control=sample_metadata.is_internal_negative_control,
            passes_reads_threshold=valid_read_count,
            passes_mutant_qc=sample_results.qc_pass,
        )

        ResultLogger.log_sample_result(sample_quality)
        return sample_quality

    def quality_control_case(self, sample_results: list[SampleQualityResult]) -> CaseQualityResult:
        internal_negative_control_pass_qc: bool = internal_negative_control_qc_pass(sample_results)
        external_negative_control_pass_qc: bool = external_negative_control_qc_pass(sample_results)

        case_pass_qc: bool = self.case_qc_pass(sample_results)

        result = CaseQualityResult(
            passes_qc=(
                case_pass_qc
                and internal_negative_control_pass_qc
                and external_negative_control_pass_qc
            ),
            internal_negative_control_pass_qc=internal_negative_control_pass_qc,
            external_negative_control_pass_qc=external_negative_control_pass_qc,
        )
        ResultLogger.log_case_result(result)
        return result

    def case_qc_pass(sample_results: list[SampleQualityResult]) -> bool:
        total_samples: int = 0
        failed_samples: int = 0

        for sample_result in sample_results:
            if (
                not sample_result.is_external_negative_control
                and not sample_result.is_internal_negative_control
            ):
                total_samples += 1
                if not sample_result.passes_qc:
                    failed_samples += 1

        return failed_samples / total_samples > MutantQC.FRACTION_OF_SAMPLES_WITH_FAILED_QC_TRESHOLD 
