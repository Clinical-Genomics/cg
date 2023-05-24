"""Functions that deals with dummy samples"""
from cg.apps.demultiplex.sample_sheet.models import (
    FlowCellSample,
    FlowCellSampleBcl2Fastq,
    FlowCellSampleDragen,
)


def dummy_sample_name(sample_name: str) -> str:
    """Convert a string to a dummy sample name

    Replace space and parentheses with dashes
    """
    return sample_name.replace(" ", "-").replace("(", "-").replace(")", "-")


def dummy_sample(
    flowcell: str, dummy_index: str, lane: int, name: str, bcl_converter: str
) -> FlowCellSample:
    """Constructs and returns a dummy sample in novaseq sample sheet format"""
    lims_flowcell_sample = {
        "bcl2fastq": FlowCellSampleBcl2Fastq,
        "dragen": FlowCellSampleDragen,
    }
    return lims_flowcell_sample[bcl_converter](
        flowcell_id=flowcell,
        lane=lane,
        sample_id=dummy_sample_name(sample_name=name),
        index=dummy_index,
        sample_name="indexcheck",
        project="indexcheck",
    )
