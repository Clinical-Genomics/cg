"""Helper functions related to the genome build."""

from cg.constants.constants import GenomeVersion
from cg.exc import CgError
from cg.store.store import Store


def get_genome_build(case_id: str, status_db: Store) -> GenomeVersion:
    """Return reference genome version for a case.
    Raises CgError if this information is missing or inconsistent for the samples linked to a case.
    """
    reference_genome: set[str] = {
        sample.reference_genome for sample in status_db.get_samples_by_case_id(case_id=case_id)
    }
    if len(reference_genome) == 1:
        return reference_genome.pop()
    if len(reference_genome) > 1:
        raise CgError(
            f"Samples linked to case {case_id} have different reference genome versions set"
        )
    raise CgError(f"No reference genome specified for case {case_id}")

