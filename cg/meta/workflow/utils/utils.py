from cg.constants.constants import ControlOptions
from cg.store.models import Case


def are_all_samples_control(case: Case) -> bool:
    """Check if all samples in a case are controls."""

    return all(
        sample.control in [ControlOptions.NEGATIVE, ControlOptions.POSITIVE]
        for sample in case.samples
    )
