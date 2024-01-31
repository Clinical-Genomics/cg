from cg.constants.constants import PrepCategory
from cg.store.models import Sample


def all_samples_are_ready_made_libraries(samples) -> bool:
    """
    Check if all samples in case are ready made libraries.

    Returns:
        bool: True if all samples are ready made libraries, False otherwise.

    """
    return all(sample.prep_category == PrepCategory.ready_made_library for sample in samples)


def standard_sequencing_qc(sample) -> bool:
    """
    Run standard sequencing qc for a sample.

    Returns:
        bool: True if sample pass the qc, False otherwise.

    """
    return all(sample.reads >= sample.expected_reads)


def express_sequencing_qc(sample) -> bool:
    """
    Run express sequencing qc for a sample.

    Returns:
        bool: True if the sample pass the qc, False otherwise.

    """
    return sample.sample.reads >= express_reads_threshold(sample)


def all_samples_have_reads(samples: list[Sample]) -> bool:
    """
    Check if all samples have reads.

    Returns:
        bool: True if all samples have reads, False otherwise.

    """
    return all(bool(sample.reads) for sample in samples)


def any_sample_has_reads(samples: list[Sample]) -> bool:
    """
    Check if any sample has reads.

    Returns:
        bool: True if any sample has reads, False otherwise.

    """
    return any(bool(sample.reads) for sample in samples)


def express_reads_threshold(sample) -> int:
    """
    Get the express reads threshold for a sample.

    Args:
        sample (Sample): The sample object.

    Returns:
        int: The express reads threshold.

    """
    return round(sample.application_version.application.target_reads / 2)


# def get_pre_analysis_quality_check_for_workflow(
#     analysis_api: AnalysisAPI,
# ) -> PreAnalysisQualityCheck:
#     pre_analysis_quality_checks: dict[AnalysisAPI, PreAnalysisQualityCheck] = {
#         BalsamicAnalysisAPI: BalsamicPreAnalysisQc,
#         BalsamicQCAnalysisAPI: BalsamicPreAnalysisQc,
#         BalsamicUmiAnalysisAPI: BalsamicPreAnalysisQc,
#         MicrosaltAnalysisAPI: MicrobialPreAnalysisQc,
#         MipDNAAnalysisAPI: MIPPreAnalysisQc,
#         MipRNAAnalysisAPI: MIPPreAnalysisQc,
#         TaxprofilerAnalysisAPI: TaxProfilerPreAnalysisQc,
#         RnafusionAnalysisAPI: RnafusionPreAnalysisQc,
#         RarediseaseAnalysisAPI: RareDiseasePreAnalysisQc,
#     }
#     pre_analysis_quality_check: PreAnalysisQualityCheck = pre_analysis_quality_checks.get(
#         type(analysis_api)
#     )
#     if not pre_analysis_quality_check:
#         raise NotImplementedError("No pre analysis quality check implemented for this workflow.")
#     return pre_analysis_quality_check
