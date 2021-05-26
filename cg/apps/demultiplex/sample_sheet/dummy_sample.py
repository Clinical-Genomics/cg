"""Functions that deals with dummy samples"""
from cg.apps.lims.samplesheet import LimsFlowcellSample


def dummy_sample_name(sample_name: str) -> str:
    """Convert a string to a dummy sample name

    Replace space and parentheses with dashes
    """
    return sample_name.replace(" ", "-").replace("(", "-").replace(")", "-")


def dummy_sample(flowcell: str, dummy_index: str, lane: int, name: str) -> LimsFlowcellSample:
    """Constructs and returns a dummy sample in novaseq sample sheet format"""
    return LimsFlowcellSample(
        flowcell_id=flowcell,
        lane=lane,
        sample_id=dummy_sample_name(sample_name=name),
        index=dummy_index,
        sample_name="indexcheck",
        project="indexcheck",
    )
