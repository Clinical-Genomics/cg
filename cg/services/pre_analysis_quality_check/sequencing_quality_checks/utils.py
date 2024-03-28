import logging

from cg.constants.constants import PrepCategory
from cg.constants.priority import Priority
from cg.store.models import Case, Sample

LOG = logging.getLogger(__name__)


def is_sample_ready_made_library(sample: Sample) -> bool:
    """
    Check if a sample is a ready made library.

    Returns:
        bool: True if the sample is a ready made library, False otherwise.

    """
    passed_quality_check: bool = sample.prep_category == PrepCategory.READY_MADE_LIBRARY
    if not passed_quality_check:
        LOG.warning(f"Sample {sample.internal_id} is not a ready made library.")
    return passed_quality_check


def case_has_express_priority(case: Case) -> bool:
    """
    Check if a case is express priority.

    Returns:
        bool: True if the case is express priority, False otherwise.

    """
    return case.priority == Priority.express


def sample_has_express_priority(sample: Sample) -> bool:
    """
    Check if a sample is express priority.

    Returns:
        bool: True if the sample is express priority, False otherwise.

    """
    return sample.priority == Priority.express


def case_is_not_express_priority(case: Case) -> bool:
    """
    Check if a case is lower than express priority.

    Returns:
        bool: True if the case is lower than express priority, False otherwise.

    """
    return case.priority != Priority.express


def ready_made_library_sample_has_enough_reads(sample: Sample) -> bool:
    """
    Check if all samples in case are ready made libraries.

    Returns:
        bool: True if all samples are ready made libraries, False otherwise.

    """
    if is_sample_ready_made_library(sample):
        if not sample.has_reads:
            LOG.warning(f"Sample {sample.internal_id} has no reads.")
        return sample.has_reads
    return False


def sample_has_enough_reads(sample: Sample) -> bool:
    """
    Run standard sequencing qc for a sample.

    Returns:
        bool: True if sample pass the qc, False otherwise.

    """
    passed_quality_check: bool = sample.reads >= sample.expected_reads_for_sample
    if not passed_quality_check:
        LOG.warning(f"Sample {sample.internal_id} has too few reads.")
    return passed_quality_check


def get_sequencing_qc_of_case(case: Case) -> bool:
    """
    Get the standard sequencing qc of a case.

    Returns:
        bool: True if the case pass the qc, False otherwise.

    """
    if case_is_not_express_priority(case):
        return all(sample_has_enough_reads(sample) for sample in case.samples)
    return False


def get_express_reads_threshold_for_sample(sample: Sample) -> int:
    """
    Get the express reads threshold for a sample.
    """

    return round(sample.application_version.application.target_reads / 2)


def express_sample_has_enough_reads(sample: Sample) -> bool:
    """
    Run express sequencing qc for a sample.

    Returns:
        bool: True if the sample pass the qc, False otherwise.

    """
    express_reads_threshold: int = get_express_reads_threshold_for_sample(sample)
    passed_quality_check: bool = sample.reads >= express_reads_threshold
    if not passed_quality_check:
        LOG.warning(f"Sample {sample.internal_id} has too few reads.")
    return passed_quality_check


def get_express_sequencing_qc_of_case(case: Case) -> bool:
    """
    Get the express sequencing qc of a case.

    Returns:
        bool: True if the case pass the qc, False otherwise.

    """
    if case_has_express_priority(case):
        return all(express_sample_has_enough_reads(sample) for sample in case.samples)
    return False


def get_express_sequencing_qc_of_sample(sample: Sample) -> bool:
    """
    Get the express sequencing qc of a sample.

    Returns:
        bool: True if the sample pass the qc, False otherwise.

    """
    if sample_has_express_priority(sample):
        return express_sample_has_enough_reads(sample)
    return False


def any_sample_in_case_has_reads(case: Case) -> bool:
    """
    Check if any sample has reads.

    Returns:
        bool: True if any sample has reads, False otherwise.

    """
    passed_quality_check: bool = any(sample.has_reads for sample in case.samples)
    if not passed_quality_check:
        LOG.warning("No samples in case have reads.")
    return passed_quality_check
