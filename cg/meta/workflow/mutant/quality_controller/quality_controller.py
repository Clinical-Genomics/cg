from pathlib import Path
from cg.meta.workflow.mutant.metrics_parser import MetricsParser, QualityMetrics, SampleMetrics
from cg.meta.workflow.mutant.quality_controller.models import (
    SampleQualityResult,
    CaseQualityResult,
    QualityResult,
)

from cg.store.api.core import Store
from cg.store.models import Sample


class QualityController:
    def __init__(self, status_db: Store):
        self.status_db = status_db

    def quality_control(self, case_results_file_path: Path) -> QualityResult:
        quality_metrics: QualityMetrics = MetricsParser.parse_sample_results(case_results_file_path)
        sample_results: list[SampleQualityResult] = self.quality_control_samples(quality_metrics)


    def quality_control_samples(self, quality_metrics: QualityMetrics) -> list[SampleQualityResult]:
        sample_results: list[SampleQualityResult] = []
        for sample_id, metrics in quality_metrics.samples.items():
            result = self.quality_control_sample(sample_id=sample_id, metrics=metrics)
            sample_results.append(result)
        return sample_results

    def quality_control_sample(self, sample_id: str, metrics: SampleMetrics) -> SampleQualityResult:
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

    # TODO
    # parse results
    # implement the QC checks
    # create a utils for the QC checks

    # # Look at how the logging is done for trailblazer

    #     sampleresults = parse_sample_results(cls, file_path) #dict[str, SampleResults]

    #     sample_list=get_sample_list(case)

    #     SampleMetadata

    #     SampleMetrics = sampleresults + SampleMetadata

    #     QualityMetrics =  samples: dict[str, SampleMetrics]
