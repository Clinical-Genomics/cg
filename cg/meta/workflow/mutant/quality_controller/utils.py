from cg.constants.constants import MutantQC
from cg.services.sequencing_qc_service.quality_checks.utils import sample_has_enough_reads
from cg.store.models import Sample


def sample_has_valid_total_reads(
    sample: Sample,
) -> bool:
    return sample_has_enough_reads(sample=sample)


def internal_negative_control_sample_has_valid_total_reads(
    sample: Sample,
) -> bool:
    return sample.reads < MutantQC.INTERNAL_NEGATIVE_CONTROL_READS_THRESHOLD


def external_negative_control_sample_has_valid_total_reads(
    sample: Sample,
) -> bool:
    return sample.reads < MutantQC.EXTERNAL_NEGATIVE_CONTROL_READS_THRESHOLD
