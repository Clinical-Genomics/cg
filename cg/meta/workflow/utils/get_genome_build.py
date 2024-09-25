"""Helper functions related to the genome build."""

from cg.constants.constants import GenomeVersion
from cg.exc import CgError
from cg.store.models import Case


def get_genome_build(case: Case) -> GenomeVersion:
    """Return reference genome version for a case.
    Raises CgError if this information is missing or inconsistent for the samples linked to a case.
    """
    reference_genome: set[str] = {sample.reference_genome for sample in case.samples}
    if len(reference_genome) == 1:
        return reference_genome.pop()
    if len(reference_genome) > 1:
        raise CgError(
            f"Samples linked to case {case.internal_id} have different reference genome versions set"
        )
    raise CgError(f"No reference genome specified for case {case.internal_id}")
