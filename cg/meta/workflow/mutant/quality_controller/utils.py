from cg.constants.constants import MutantQC
from cg.services.sequencing_qc_service.quality_checks.utils import sample_has_enough_reads
from cg.store.models import Sample


def has_valid_total_reads(
    sample: Sample,
    external_negative_control: bool = False,
    internal_negative_control: bool = False,
) -> bool:
    if external_negative_control:
        return external_negative_control_sample_has_valid_total_reads(reads=sample.reads)

    if internal_negative_control:
        return internal_negative_control_sample_has_valid_total_reads(reads=sample.reads)

    return sample_has_enough_reads(sample=sample)


def external_negative_control_sample_has_valid_total_reads(reads: int) -> bool:
    return reads < MutantQC.EXTERNAL_NEGATIVE_CONTROL_READS_THRESHOLD


def internal_negative_control_sample_has_valid_total_reads(reads: int) -> bool:
    return reads < MutantQC.INTERNAL_NEGATIVE_CONTROL_READS_THRESHOLD
