from cg.apps.lims.api import LimsAPI
from cg.constants.constants import MutantQC
from cg.meta.workflow.mutant.constants import QUALITY_REPORT_FILE_NAME
from cg.meta.workflow.mutant.metadata_parser.metadata_parser import MetadataParser
from cg.meta.workflow.mutant.metadata_parser.models import SampleMetadata, SamplesMetadataMetrics
from cg.meta.workflow.mutant.metrics_parser.metrics_parser import MetricsParser
from cg.meta.workflow.mutant.metrics_parser.models import SamplesResultsMetrics
from cg.meta.workflow.mutant.quality_controller.models import (
    QualityMetrics,
    SampleQualityResult,
)
from cg.store.models import Case, Sample

from pathlib import Path

from cg.store.store import Store


def has_valid_total_reads(sample_metadata: SampleMetadata) -> bool:
    if sample_metadata.is_external_negative_control:
        if is_valid_total_reads_for_external_negative_control(reads=sample_metadata.reads):
            return True
        else:
            return False
            # TODO: KRAKEN

    if sample_metadata.is_internal_negative_control:
        return is_valid_total_reads_for_internal_negative_control(reads=sample_metadata.reads)

    return is_valid_total_reads(
        reads=sample_metadata.reads,
        target_reads=sample_metadata.target_reads,
        threshold_percentage=sample_metadata.percent_reads_guaranteed,
    )


def is_valid_total_reads(reads: int, target_reads: int, threshold_percentage: int) -> bool:
    return reads > target_reads * threshold_percentage / 100


def is_valid_total_reads_for_external_negative_control(reads: int) -> bool:
    return reads < MutantQC.EXTERNAL_NEGATIVE_CONTROL_READS_THRESHOLD


def is_valid_total_reads_for_internal_negative_control(reads: int) -> bool:
    return reads < MutantQC.INTERNAL_NEGATIVE_CONTROL_READS_THRESHOLD


def internal_negative_control_qc_pass(results: list[SampleQualityResult]) -> bool:
    for result in results:
        if result.is_internal_negative_control:
            internal_negative_control_result = result
    return internal_negative_control_result.passes_qc


def external_negative_control_qc_pass(results: list[SampleQualityResult]) -> bool:
    for result in results:
        if result.is_external_negative_control:
            external_negative_control_result = result
    return external_negative_control_result.passes_qc


def get_sample_target_reads(sample: Sample) -> int:
    return sample.application_version.application.target_reads


def get_percent_reads_guaranteed(sample: Sample) -> int:
    return sample.application_version.application.percent_reads_guaranteed


def translate_samples_results(
    raw_samples_results: SamplesResultsMetrics, samples_metadata: SamplesMetadataMetrics
):
    sample_name_to_id_mapping = {}
    for sample_metadata in samples_metadata.samples.values():
        sample_name_to_id_mapping[sample_metadata.sample_name] = sample_metadata.sample_internal_id

    translated_samples_results = {}
    for key, value in raw_samples_results.samples.items():
        new_key: str = sample_name_to_id_mapping.get(key, key)
        translated_samples_results[new_key] = value

    samples_results = {"samples": translated_samples_results}

    return SamplesResultsMetrics.model_validate(samples_results)


def get_quality_metrics(
    case_results_file_path: Path, case: Case, status_db: Store, lims: LimsAPI
) -> QualityMetrics | None:
    raw_samples_results: SamplesResultsMetrics = MetricsParser.parse_samples_results(
        case_results_file_path
    )

    samples_metadata: SamplesMetadataMetrics = MetadataParser(
        status_db=status_db, lims=lims
    ).parse_metadata(case)

    samples_results = translate_samples_results(raw_samples_results, samples_metadata)

    if not samples_metadata:
        return None
    else:
        quality_metrics = {"samples_results": samples_results, "samples_metadata": samples_metadata}
        return QualityMetrics.model_validate(quality_metrics)


def get_report_path(case_path: Path) -> Path:
    return case_path.joinpath(QUALITY_REPORT_FILE_NAME)
