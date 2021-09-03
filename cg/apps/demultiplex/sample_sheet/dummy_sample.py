"""Functions that deals with dummy samples"""
from cg.apps.lims.samplesheet import (
    LimsFlowcellSample,
    LimsFlowcellSampleBcl2Fastq,
    LimsFlowcellSampleDragen,
)


def dummy_sample_name(sample_name: str) -> str:
    """Convert a string to a dummy sample name

    Replace space and parentheses with dashes
    """
    return sample_name.replace(" ", "-").replace("(", "-").replace(")", "-")


def dummy_sample(
    flowcell: str, dummy_index: str, lane: int, name: str, bcl_converter: str
) -> LimsFlowcellSample:
    """Constructs and returns a dummy sample in novaseq sample sheet format"""
    lims_flowcell_sample = {
        "bcl2fastq": LimsFlowcellSampleBcl2Fastq,
        "dragen": LimsFlowcellSampleDragen,
    }
    return lims_flowcell_sample[bcl_converter](
        flowcell_id=flowcell,
        lane=lane,
        sample_id=dummy_sample_name(sample_name=name),
        index=dummy_index,
        sample_name="indexcheck",
        project="indexcheck",
    )
