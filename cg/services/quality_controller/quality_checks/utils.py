import logging

from cg.constants.constants import PrepCategory
from cg.constants.priority import Priority
from cg.store.models import Case, Sample

LOG = logging.getLogger(__name__)


def case_pass_sequencing_qc(case: Case) -> bool:
    """
    Get the standard sequencing qc of a case. If the case is express priority, the express qc is
    used. If the case is a ready made library, the ready made library qc is used.
    """
    if is_case_ready_made_library(case):
        return ready_made_library_case_pass_sequencing_qc(case)
    if case_has_express_priority(case):
        return express_case_pass_sequencing_qc(case)
    return all(sample_has_enough_reads(sample) for sample in case.samples)


def express_case_pass_sequencing_qc(case: Case) -> bool:
    """
    Checks if all samples in an express case have enough reads.
    """

    return all(express_sample_has_enough_reads(sample) for sample in case.samples)


def express_sample_pass_sequencing_qc(sample: Sample) -> bool:
    return express_sample_has_enough_reads(sample)


def sample_pass_sequencing_qc(sample: Sample) -> bool:
    """
    Get the standard sequencing qc of a sample.
    """
    if is_sample_express_priority(sample):
        return express_sample_pass_sequencing_qc(sample)
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


def any_sample_in_case_has_reads(case: Case) -> bool:
    """
    Check if any sample has reads.
    """
    passed_quality_check: bool = any(sample.has_reads for sample in case.samples)
    if not passed_quality_check:
        LOG.warning("No samples in case have reads.")
    return passed_quality_check


def case_has_express_priority(case: Case) -> bool:
    """
    Check if a case is express priority.
    """
    return case.priority == Priority.express


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


def get_express_reads_threshold_for_sample(sample: Sample) -> int:
    """
    Get the express reads threshold for a sample.
    """

    return round(sample.application_version.application.target_reads / 2)


def is_sample_ready_made_library(sample: Sample) -> bool:
    return sample.prep_category == PrepCategory.READY_MADE_LIBRARY


def is_case_ready_made_library(case: Case) -> bool:
    """
    Check if all samples in case are ready made libraries.
    """
    return all(is_sample_ready_made_library(sample) for sample in case.samples)


def ready_made_library_sample_has_enough_reads(sample: Sample) -> bool:
    """
    Check if all samples in case are ready made libraries.
    """

    if not sample.has_reads:
        LOG.warning(f"Sample {sample.internal_id} has no reads.")
    return sample.has_reads


def sample_has_enough_reads(sample: Sample) -> bool:
    """
    Run standard sequencing qc for a sample.
    """
    enough_reads: bool = sample.reads >= sample.expected_reads_for_sample
    if not enough_reads:
        LOG.warning(f"Sample {sample.internal_id} has too few reads.")
    return enough_reads


def is_sample_express_priority(sample: Sample) -> bool:
    """
    Check if a sample is express priority.
    """
    return sample.priority == Priority.express
