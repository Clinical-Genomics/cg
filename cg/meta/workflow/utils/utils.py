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
        0: TrailblazerPriority.RESEARCH,
        1: TrailblazerPriority.STANDARD,
        2: TrailblazerPriority.PRIORITY,
        3: TrailblazerPriority.EXPRESS,
    }[priority]