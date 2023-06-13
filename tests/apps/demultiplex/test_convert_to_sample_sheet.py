from pathlib import Path
from typing import List
from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import (
    SampleSheetCreatorV1,
    SampleSheetCreatorV2,
)
from cg.apps.demultiplex.sample_sheet.models import (
    SampleSheet,
    FlowCellSampleNovaSeq6000Bcl2Fastq,
    FlowCellSampleNovaSeq6000Dragen,
    FlowCellSampleNovaSeqX,
)
from cg.apps.demultiplex.sample_sheet.validate import validate_sample_sheet


def test_convert_to_bcl2fastq_sheet(
    novaseq_bcl2fastq_sample_sheet_creator: SampleSheetCreatorV1, project_dir: Path
):
    """Test that a created Bcl2fastq sample sheet has samples."""
    # GIVEN a sample sheet object populated with Bcl2fastq samples
    assert novaseq_bcl2fastq_sample_sheet_creator.lims_samples

    # WHEN converting to a sample sheet
    sample_sheet: List[List[str]] = novaseq_bcl2fastq_sample_sheet_creator.construct_sample_sheet()

    # THEN assert a correctly formatted sample sheet was created
    sample_sheet_object: SampleSheet = validate_sample_sheet(
        sample_sheet_content=sample_sheet,
        sample_type=FlowCellSampleNovaSeq6000Bcl2Fastq,
    )
    assert sample_sheet_object.samples


def test_convert_to_dragen_sheet(
    novaseq_dragen_sample_sheet_creator: SampleSheetCreatorV1, project_dir: Path
):
    """Test that a created Dragen sample sheet has samples."""
    # GIVEN a sample sheet object populated with Dragen samples
    assert novaseq_dragen_sample_sheet_creator.lims_samples

    # WHEN converting to a sample sheet
    sample_sheet: List[List[str]] = novaseq_dragen_sample_sheet_creator.construct_sample_sheet()

    # THEN assert a correctly formatted sample sheet was created
    sample_sheet_object: SampleSheet = validate_sample_sheet(
        sample_sheet_content=sample_sheet,
        sample_type=FlowCellSampleNovaSeq6000Dragen,
    )
    assert sample_sheet_object.samples


def test_convert_to_novaseq_x_sheet(
    novaseq_x_sample_sheet_creator: SampleSheetCreatorV2, project_dir: Path
):
    """Test that a created NovaSeqX sample sheet has samples."""
    # GIVEN a sample sheet object populated with Dragen samples
    assert novaseq_x_sample_sheet_creator.lims_samples

    # WHEN converting to a sample sheet
    sample_sheet: List[List[str]] = novaseq_x_sample_sheet_creator.construct_sample_sheet()

    # THEN assert a correctly formatted sample sheet was created
    sample_sheet_object: SampleSheet = validate_sample_sheet(
        sample_sheet_content=sample_sheet,
        sample_type=FlowCellSampleNovaSeqX,
    )
    assert sample_sheet_object.samples
