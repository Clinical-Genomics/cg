"""Tests for the SampleSheetCreator classes."""

from pathlib import Path

from cg.apps.demultiplex.sample_sheet.read_sample_sheet import get_flow_cell_samples_from_content
from cg.apps.demultiplex.sample_sheet.sample_models import FlowCellSample
from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import SampleSheetCreator


def test_construct_bcl_convert_sheet(
    bcl_convert_sample_sheet_creator: SampleSheetCreator, project_dir: Path
):
    """Test that a created BCL Convert sample sheet has samples."""
    # GIVEN a BCL convert sample sheet creator populated with BCL convert samples
    assert bcl_convert_sample_sheet_creator.lims_samples

    # WHEN building the sample sheet content
    content: list[list[str]] = bcl_convert_sample_sheet_creator.construct_sample_sheet()

    # THEN a correctly formatted sample sheet was created
    samples: list[FlowCellSample] = get_flow_cell_samples_from_content(content)
    assert samples
