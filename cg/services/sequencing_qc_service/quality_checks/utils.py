import logging

from cg.constants.devices import DeviceType
from cg.constants.priority import Priority
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.exc import ApplicationDoesNotHaveHiFiYieldError
from cg.store.models import Case, Sample

LOG = logging.getLogger(__name__)


def case_pass_sequencing_qc_on_reads(case: Case) -> bool:
    """
    Get the sequencing QC of a case. The checks are performed in the following order:
    1. If the case is a ready-made library, the ready made library QC is used.
    2. If the case is express priority, the express QC is used.
    3. If neither of the above conditions are met, it checks if all samples have enough reads.

    The order of these checks is important because the ready-made library QC is more relaxed,
    and should be checked before the express QC, and the express QC should be checked before the
    standard QC.
    """
    if is_case_ready_made_library(case):
        return ready_made_library_case_pass_sequencing_qc(case)
    if is_case_express_priority(case):
        return express_case_pass_sequencing_qc_on_reads(case)
    return all(sample_has_enough_reads(sample) for sample in case.samples)


def case_pass_sequencing_qc_on_hifi_yield(case: Case) -> bool:
    """
    Get the sequencing QC of a case using yield. The checks are performed in the following order:
    1. If the case is express priority, the express QC is used.
    2. If the above condition is not met then it checks if all samples have enough yield.

    The express QC should be checked before the standard QC.
    """
    if is_case_express_priority(case):
        return express_case_pass_sequencing_qc_on_hifi_yield(case)
    return all(sample_has_enough_hifi_yield(sample) for sample in case.samples)


def express_case_pass_sequencing_qc_on_reads(case: Case) -> bool:
    """
    Checks if all samples in an express case have enough reads.
    """
    return all(express_sample_has_enough_reads(sample) for sample in case.samples)


def express_case_pass_sequencing_qc_on_hifi_yield(case: Case) -> bool:
    """
    Checks if all samples in an express case have enough hifi yield.
    """
    return all(express_sample_has_enough_yield(sample) for sample in case.samples)


def express_sample_pass_sequencing_qc_on_reads(sample: Sample) -> bool:
    return express_sample_has_enough_reads(sample)


def express_sample_has_enough_reads(sample: Sample) -> bool:
    """
    Checks if given express sample has enough reads. Gets the threshold from the sample's
    application version.
    """
    express_reads_threshold: int = get_express_reads_threshold_for_sample(sample)
    enough_reads: bool = sample.reads >= express_reads_threshold
    if not enough_reads:
        LOG.warning(f"Sample {sample.internal_id} has too few reads.")
    return enough_reads


def express_sample_has_enough_yield(sample: Sample) -> bool:
    if not sample.hifi_yield:
        LOG.debug(f"Sample {sample.internal_id} has no hifi yield.")
        return False

    express_yield_threshold: int = get_express_yield_threshold_for_sample(sample)
    enough_yield: bool = sample.hifi_yield >= express_yield_threshold
    if not enough_yield:
        LOG.warning(f"Sample {sample.internal_id} does not have enough yield.")
    return enough_yield


def sample_pass_sequencing_qc_on_reads(sample: Sample) -> bool:
    """
    Get the standard sequencing QC of a sample. The checks are performed in the following order:
    1. If the sample is express priority, the express QC is used.
    2. If the sample is a ready-made library, the ready made library QC is used.
    3. If neither of the above conditions are met, it checks if the sample has enough reads.

    The order of these checks is important because the express QC is more relaxed, and should be
    checked before the standard QC.
    """
    if is_sample_express_priority(sample):
        return express_sample_pass_sequencing_qc_on_reads(sample)
    if is_sample_ready_made_library(sample):
        return ready_made_library_sample_has_enough_reads(sample)
    return sample_has_enough_reads(sample)


def ready_made_library_case_pass_sequencing_qc(case: Case) -> bool:
    """
    Checks if the sum of reads of all samples in a ready made library case is enough.

    The threshold is the expected reads for any sample in the case.
    """
    threshold: int = case.samples[0].expected_reads_for_sample
    reads: int = sum(sample.reads for sample in case.samples)
    enough_reads: bool = reads >= threshold
    if not enough_reads:
        LOG.warning(f"Case {case.internal_id} has too few reads.")
    return enough_reads


def all_samples_in_case_have_reads(case: Case) -> bool:
    """
    Check if all samples have reads.
    """
    passed_quality_check: bool = all(sample.has_reads for sample in case.samples)
    if not passed_quality_check:
        LOG.warning("Not all samples in case have reads.")
    return passed_quality_check


def any_sample_in_case_has_reads(case: Case) -> bool:
    """
    Check if any sample has reads.
    """
    passed_quality_check: bool = any(sample.has_reads for sample in case.samples)
    if not passed_quality_check:
        LOG.warning("No samples in case have reads.")
    return passed_quality_check


def raw_data_case_pass_qc(case: Case) -> bool:
    if is_case_ready_made_library(case):
        return ready_made_library_case_pass_sequencing_qc(case)
    if is_first_sample_yield_based_and_processed(case):
        return all(sample_has_enough_hifi_yield(sample) for sample in case.samples)
    elif is_first_sample_reads_based_and_processed(case):
        return all(sample_has_enough_reads(sample) for sample in case.samples)
    LOG.warning(f"Not all samples for case {case.internal_id} have been post-processed.")
    return False


def is_first_sample_yield_based_and_processed(case: Case) -> bool:
    sample: Sample = case.samples[0]
    if metrics := sample.sample_run_metrics:
        return metrics[0].type == DeviceType.PACBIO
    return False


def is_first_sample_reads_based_and_processed(case: Case) -> bool:
    sample: Sample = case.samples[0]
    if metrics := sample.sample_run_metrics:
        return metrics[0].type == DeviceType.ILLUMINA
    return False


def is_case_express_priority(case: Case) -> bool:
    """
    Check if a case is express priority.
    """
    return case.priority == Priority.express


def get_express_reads_threshold_for_sample(sample: Sample) -> int:
    """
    Get the express reads threshold for a sample.
    """
    return round(sample.application_version.application.target_reads / 2)


def get_express_yield_threshold_for_sample(sample: Sample) -> int:
    if threshold := sample.application_version.application.expected_express_hifi_yield:
        return threshold
    else:
        raise ApplicationDoesNotHaveHiFiYieldError(
            f"Application for sample {sample.internal_id} does not have target HiFi yield."
        )


def is_sample_ready_made_library(sample: Sample) -> bool:
    return sample.prep_category == SeqLibraryPrepCategory.READY_MADE_LIBRARY


def is_case_ready_made_library(case: Case) -> bool:
    """
    Check if all samples in case are ready made libraries.
    """
    return all(is_sample_ready_made_library(sample) for sample in case.samples)


def ready_made_library_sample_has_enough_reads(sample: Sample) -> bool:
    """
    Check if a given sample from a ready made library has enough reads.
    """
    if not sample.has_reads:
        LOG.warning(f"Sample {sample.internal_id} has no reads.")
    return sample.has_reads


def sample_has_enough_reads(sample: Sample) -> bool:
    """
    Return True if:
    - The sample has at least the expected number of reads, or
    - The sample has already been delivered.
    """
    enough_reads: bool = (
        sample.reads >= sample.expected_reads_for_sample or sample.delivered_at is not None
    )  # TODO why is this red?
    if not enough_reads:
        LOG.warning(f"Sample {sample.internal_id} has too few reads.")
    return enough_reads


def sample_has_enough_hifi_yield(sample: Sample) -> bool:
    """
    Return true if the sample's HiFi yield is greater than or equal to the threshold.
    Returns true if sample has already been delivered.
    Returns false if the HiFi yield is lower than the threshold or None.
    Raises:
        ApplicationDoesNotHaveHiFiYieldError if the sample doesn't have expected HiFi yield.
    """
    if not sample.expected_hifi_yield:
        raise ApplicationDoesNotHaveHiFiYieldError(
            f"Application for sample {sample.internal_id} does not have target HiFi yield."
        )

    if not sample.hifi_yield:
        LOG.debug(f"Sample {sample.internal_id} has no hifi yield.")
        return False

    enough_hifi_yield: bool = (
        sample.hifi_yield >= sample.expected_hifi_yield or sample.delivered_at is not None
    )
    if not enough_hifi_yield:
        LOG.warning(f"Sample {sample.internal_id} does not have enough HiFi yield.")
    return enough_hifi_yield


def is_sample_express_priority(sample: Sample) -> bool:
    """
    Check if a sample is express priority.
    """
    return sample.priority == Priority.express
