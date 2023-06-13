"""Tests for functions related to dummy samples."""
from cg.apps.demultiplex.sample_sheet.dummy_sample import dummy_sample, dummy_sample_name
from cg.apps.demultiplex.sample_sheet.index import Index
from cg.apps.demultiplex.sample_sheet.models import (
    FlowCellSample,
    FlowCellSampleNovaSeq6000Bcl2Fastq,
)


def test_get_dummy_sample_name():
    """Test that a dummy sample has the correct name."""
    # GIVEN a raw sample name from the index file
    raw_sample_name = "D10 - D710-D504 (TCCGCGAA-GGCTCTGA)"

    # WHEN converting it to a dummy sample name
    sample_name: str = dummy_sample_name(raw_sample_name)

    # THEN that the correct name was created
    assert sample_name == "D10---D710-D504--TCCGCGAA-GGCTCTGA-"


def test_get_dummy_sample(bcl2fastq_flow_cell_id: str, index_obj: Index):
    """Test that a created dummy samples has the correct id."""
    # GIVEN some dummy sample data

    # WHEN creating the dummy sample for a bcl2fastq sample sheet
    dummy_flow_cell_sample: FlowCellSample = dummy_sample(
        flow_cell_id=bcl2fastq_flow_cell_id,
        dummy_index=index_obj.sequence,
        lane=1,
        name=index_obj.name,
        sample_type=FlowCellSampleNovaSeq6000Bcl2Fastq,
    )

    # THEN that the sample id was correct
    assert dummy_flow_cell_sample.sample_id == dummy_sample_name(index_obj.name)
