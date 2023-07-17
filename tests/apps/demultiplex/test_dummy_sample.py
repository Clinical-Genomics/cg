"""Tests for functions related to dummy samples."""
from cg.apps.demultiplex.sample_sheet.dummy_sample import get_dummy_sample, get_dummy_sample_name
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
    dummy_sample_name: str = get_dummy_sample_name(sample_name=raw_sample_name)

    # THEN the name had spaces and parentheses replaced by dashes
    assert dummy_sample_name == "D10---D710-D504--TCCGCGAA-GGCTCTGA-"


def test_get_dummy_sample(bcl2fastq_flow_cell_id: str, valid_index: Index):
    """Test that a created dummy samples has the correct id."""
    # GIVEN some dummy sample data

    # WHEN creating the dummy sample for a bcl2fastq sample sheet
    dummy_flow_cell_sample: FlowCellSample = get_dummy_sample(
        flow_cell_id=bcl2fastq_flow_cell_id,
        dummy_index=valid_index.sequence,
        lane=1,
        name=valid_index.name,
        sample_type=FlowCellSampleNovaSeq6000Bcl2Fastq,
    )

    # THEN the sample id was correct
    assert dummy_flow_cell_sample.sample_id == get_dummy_sample_name(valid_index.name)
