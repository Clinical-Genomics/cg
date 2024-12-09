from cg.constants.constants import ControlOptions
from cg.constants.priority import TrailblazerPriority
from cg.store.models import Case


def are_all_samples_control(case: Case) -> bool:
    """Check if all samples in a case are controls."""

    return all(
        sample.control in [ControlOptions.NEGATIVE, ControlOptions.POSITIVE]
        for sample in case.samples
    )


MAP_TO_TRAILBLAZER_PRIORITY: dict[int, TrailblazerPriority] = {
    0: TrailblazerPriority.LOW,
    1: TrailblazerPriority.NORMAL,
    2: TrailblazerPriority.HIGH,
    3: TrailblazerPriority.EXPRESS,
    4: TrailblazerPriority.NORMAL,
}
