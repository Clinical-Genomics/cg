"""Functions that deals with dummy samples"""

from cg.apps.demultiplex.sample_sheet.models import FlowCellSample


def dummy_sample_name(sample_name: str) -> str:
    """Convert a string to a dummy sample name replacing spaces and parentheses with dashes."""
    return sample_name.replace(" ", "-").replace("(", "-").replace(")", "-")


def dummy_sample(dummy_index: str, lane: int, name: str) -> FlowCellSample:
    """Constructs and returns a dummy sample in Novaseq sample sheet format."""
    return FlowCellSample(
        lane=lane,
        sample_id=dummy_sample_name(sample_name=name),
        index=dummy_index,
        override_cycles="Y151;I10;I10;Y151",
    )
