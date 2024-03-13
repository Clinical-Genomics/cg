from pathlib import Path
from cg.meta.workflow.mutant.metadata_parser.metadata_parser import MetadataParser
from cg.meta.workflow.mutant.metrics_parser import MetricsParser, SampleMetrics
from cg.meta.workflow.mutant.metrics_parser.models import SampleResultsMetrics
from cg.meta.workflow.mutant.quality_controller.models import (
    SampleQualityResult,
    CaseQualityResult,
    QualityResult,
)

from cg.meta.workflow.mutant.quality_controller.utils import (
    external_negative_control_pass_qc,
    get_percent_reads_guaranteed,
    get_sample_target_reads,
    is_sample_external_negative_control,
    is_sample_negative_control,
    is_valid_total_reads,
    is_valid_total_reads_for_external_negative_control,
)
from cg.store.api.core import Store
from cg.store.models import Sample


class QualityController:
    def __init__(self, status_db: Store):
        # self.status_db = status_db
        self.metadata_parser = MetadataParser(status_db)

    def quality_control(self, case_results_file_path: Path, case: Case) -> QualityResult:
        samples_results: SampleResultsMetrics = MetricsParser.parse_samples_results(
            case_results_file_path
        )

        samples_metadata: 

        sample_results: list[SampleQualityResult] = self.quality_control_samples()
        case_result: CaseQualityResult = self.quality_control_case(sample_results)
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
        for sample_id, metrics in quality_metrics.samples.items():
            result = self.quality_control_sample(sample_id=sample_id, metrics=metrics)
            sample_results.append(result)
        return sample_results

    def quality_control_sample(self, sample_id: str, metrics: SampleMetrics) -> SampleQualityResult:
        valid_read_count: bool = self.has_valid_total_reads(sample_id)
        # valid_10x_coverage: bool = has_valid_10x_coverage(metrics)
        mutant_qc_pass: bool = self.sample_qc_pass(sample_id, metrics)

        sample: Sample = self.status_db.get_sample_by_internal_id(sample_id)

        if is_control := is_sample_negative_control(sample):
            sample_quality = SampleQualityResult(
                sample_id=sample_id,
                passes_qc=valid_read_count,
                is_control=is_control,
                passes_reads_qc=valid_read_count,
            )
            ResultLogger.log_sample_result(sample_quality)
            return sample_quality

        sample_passes_qc: bool = valid_read_count and mutant_qc_pass

        sample_quality = SampleQualityResult(
            sample_id=sample_id,
            passes_qc=sample_passes_qc,
            is_control=is_control,
            passes_reads_qc=valid_read_count,
            passes_mutant_qc=mutant_qc_pass,
        )
        ResultLogger.log_sample_result(sample_quality)
        return sample_quality

    def has_valid_total_reads(self, sample_id: str) -> bool:
        sample: Sample = self.status_db.get_sample_by_internal_id(sample_id)
        target_reads: int = get_sample_target_reads(sample)
        percent_reads_guaranteed: int = get_percent_reads_guaranteed(sample)
        sample_reads: int = sample.reads

        if is_sample_external_negative_control(sample):
            if is_valid_total_reads_for_external_negative_control(
                reads=sample_reads, target_reads=target_reads
            ):
                return True
            else:
                return None
                # TODO: KRAKEN

        return is_valid_total_reads(
            reads=sample_reads,
            target_reads=target_reads,
            threshold_percentage=percent_reads_guaranteed,
        )

    def sample_qc_pass(self, sample_id: str, metrics):
        sample: Sample = self.status_db.get_sample_by_internal_id(sample_id)

        sample_metrics = metrics[sample.sample_name]

        return sample_metrics.SampleResults.qc_pass

    def quality_control_case(self, sample_results: list[SampleQualityResult]) -> CaseQualityResult:
        external_control_pass_qc: bool = external_negative_control_pass_qc(sample_results)
        case_pass_qc: bool = self.case_qc_pass(sample_results)
        case_passes_qc: bool = control_pass_qc and case_pass_qc

        result = CaseQualityResult(
            passes_qc=case_passes_qc,
            control_passes_qc=external_control_pass_qc,
        )
        ResultLogger.log_case_result(result)
        return result

    def case_qc_pass(sample_results: list[SampleQualityResult]) -> bool:
        total_samples: int = len(sample_results)

        failed_samples: int = 0

        for sample_result in sample_results:
            if not sample_result.passes_qc:
                failed_samples = failed_samples + 1

        if failed_samples / total_samples > 0.2:
            return False
        else:
            return True

    # TODO
    # parse results - check
    # implement the QC checks - check
    # create a utils for the QC checks  - check

    # # Look at how the logging is done for trailblazer

    #     sampleresults = parse_sample_results(cls, file_path) #dict[str, SampleResults]

    #     sample_list=get_sample_list(case)

    #     SampleMetadata

    #     SampleMetrics = sampleresults + SampleMetadata

    #     QualityMetrics =  samples: dict[str, SampleMetrics]
