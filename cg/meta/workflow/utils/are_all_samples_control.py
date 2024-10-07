from cg.constants.constants import ControlOptions
from cg.store.models import Case


def are_all_samples_control(case: Case) -> bool:
    return all(
        sample.control in [ControlOptions.NEGATIVE, ControlOptions.POSITIVE]
        for sample in case.samples
    )
