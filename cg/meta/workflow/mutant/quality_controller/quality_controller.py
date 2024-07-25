from pathlib import Path
from cg.apps.lims.api import LimsAPI
from cg.constants.constants import MutantQC
from cg.exc import CgError
from cg.meta.workflow.mutant.metrics_parser.models import SampleResults
from cg.meta.workflow.mutant.quality_controller.models import (
    QualityMetrics,
    SampleQualityResults,
    CaseQualityResult,
    QualityResult,
    SamplesQualityResults,
)

from cg.meta.workflow.mutant.quality_controller.result_logger import ResultLogger
from cg.meta.workflow.mutant.quality_controller.report_generator import ReportGenerator
from cg.meta.workflow.mutant.quality_controller.utils import (
    get_quality_metrics,
    get_report_path,
    has_valid_total_reads,
)
from cg.store.models import Case, Sample
from cg.store.store import Store


class QualityController:
    def __init__(
        self,
        status_db: Store,
        lims: LimsAPI,
        report_generator: ReportGenerator,
        result_logger: ResultLogger,
    ) -> None:
        self.status_db: Store = status_db
        self.lims: LimsAPI = lims
        self.report_generator: ReportGenerator = report_generator
        self.result_logger: ResultLogger = result_logger

    def quality_control(
        self, case: Case, case_path: Path, case_results_file_path: Path
    ) -> QualityResult:
        """Perform QC check on a case and generate the QC_report."""
        try:
            quality_metrics: QualityMetrics = get_quality_metrics(
                case_results_file_path=case_results_file_path,
                case=case,
                status_db=self.status_db,
                lims=self.lims,
            )
        except Exception as exception_object:
            raise CgError from exception_object

        samples_quality_results: SamplesQualityResults = self.quality_control_samples(
            quality_metrics=quality_metrics
        )
        case_quality_result: CaseQualityResult = self.quality_control_case(samples_quality_results)

        self.report_generator.write_report(
            case_path=case_path,
            samples_quality_results=samples_quality_results,
            case_quality_result=case_quality_result,
        )

        report_file_path = self.report_generator.get_report_path()

        self.result_logger.log_results(
            case_quality_result=case_quality_result,
            samples_quality_results=samples_quality_results,
            report_file_path=report_file_path,
        )

        summary: str = self.report_generator.get_summary(
            case_quality_result=case_quality_result,
            samples_quality_results=samples_quality_results,
            report_file_path=report_file_path,
        )

        return QualityResult(
            case_quality_result=case_quality_result,
            samples_quality_results=samples_quality_results,
            summary=summary,
        )

    def quality_control_samples(self, quality_metrics: QualityMetrics) -> SamplesQualityResults:
        samples_quality_results: list[SampleQualityResults] = []
        for sample in quality_metrics.pool.samples:
            sample_results: SampleResults = quality_metrics.results[sample.internal_id]
            sample_quality_results: SampleQualityResults = self.quality_control_sample(
                sample=sample, sample_results=sample_results
            )
            samples_quality_results.append(sample_quality_results)

        internal_negative_control_sample: Sample = quality_metrics.pool.internal_negative_control
        internal_negative_control_sample_results: SampleResults = quality_metrics.results[
            internal_negative_control_sample.internal_id
        ]
        internal_negative_control_quality_metrics: (
            SampleQualityResults
        ) = self.quality_control_sample(
            sample=internal_negative_control_sample,
            sample_results=internal_negative_control_sample_results,
        )

        external_negative_control_sample: Sample = quality_metrics.pool.external_negative_control
        external_negative_control_sample_results: SampleResults = quality_metrics.results[
            external_negative_control_sample.internal_id
        ]
        external_negative_control_quality_metrics: (
            SampleQualityResults
        ) = self.quality_control_sample(
            sample=external_negative_control_sample,
            sample_results=external_negative_control_sample_results,
        )

        return SamplesQualityResults(
            samples=samples_quality_results,
            internal_negative_control=internal_negative_control_quality_metrics,
            external_negative_control=external_negative_control_quality_metrics,
        )

    def quality_control_sample(
        self,
        sample: Sample,
        sample_results: SampleResults,
        external_negative_control: bool = False,
        internal_negative_control: bool = False,
    ) -> SampleQualityResults:
        sample_has_valid_total_reads: bool = has_valid_total_reads(
            sample=sample,
            external_negative_control=external_negative_control,
            internal_negative_control=internal_negative_control,
        )
        sample_passes_qc: bool = sample_has_valid_total_reads and sample_results.qc_pass

        sample_quality = SampleQualityResults(
            sample_id=sample.internal_id,
            passes_qc=sample_passes_qc,
            passes_reads_threshold=sample_has_valid_total_reads,
            passes_mutant_qc=sample_results.qc_pass,
        )

        ResultLogger.log_sample_result(sample_quality)
        return sample_quality

    def quality_control_case(
        self, samples_quality_results: SamplesQualityResults
    ) -> CaseQualityResult:
        external_negative_control_pass_qc: (
            bool
        ) = samples_quality_results.external_negative_control.passes_qc
        internal_negative_control_pass_qc: (
            bool
        ) = samples_quality_results.internal_negative_control.passes_qc

        samples_pass_qc: bool = self.samples_pass_qc(
            samples_quality_results=samples_quality_results
        )

        result = CaseQualityResult(
            passes_qc=(
                samples_pass_qc
                and internal_negative_control_pass_qc
                and external_negative_control_pass_qc
            ),
            internal_negative_control_passes_qc=internal_negative_control_pass_qc,
            external_negative_control_passes_qc=external_negative_control_pass_qc,
        )
        ResultLogger.log_case_result(result)
        return result

    def samples_pass_qc(self, samples_quality_results: SamplesQualityResults) -> bool:
        return (
            samples_quality_results.failed_samples_count
            / samples_quality_results.total_samples_count
            < MutantQC.FRACTION_OF_SAMPLES_WITH_FAILED_QC_TRESHOLD
        )
