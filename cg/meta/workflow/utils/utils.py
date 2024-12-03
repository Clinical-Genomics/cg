from cg.constants.constants import ControlOptions
from cg.constants.priority import TrailblazerPriority
from cg.store.models import Case


def are_all_samples_control(case: Case) -> bool:
    """Check if all samples in a case are controls."""

    return all(
        sample.control in [ControlOptions.NEGATIVE, ControlOptions.POSITIVE]
        for sample in case.samples
    )


def map_to_trailblazer_priority(priority: int) -> TrailblazerPriority:
    """Map a priority to a Trailblazer priority."""
    return {
        0: TrailblazerPriority.LOW,
        1: TrailblazerPriority.NORMAL,
        2: TrailblazerPriority.HIGH,
        3: TrailblazerPriority.EXPRESS,
        4: TrailblazerPriority.NORMAL,
    }[priority]
