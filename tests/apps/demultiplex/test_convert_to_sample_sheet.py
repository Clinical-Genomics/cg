from pathlib import Path
from typing import List

from cg.apps.demultiplex.sample_sheet.novaseq_sample_sheet import SampleSheetCreator
from cg.apps.demultiplex.sample_sheet.models import SampleSheet
from cg.apps.demultiplex.sample_sheet.validate import validate_sample_sheet


def test_convert_to_bcl2fastq_sheet(
    novaseq_bcl2fastq_sample_sheet_object: SampleSheetCreator, project_dir: Path
):
    """Test that a created bcl2fastq sample sheet has samples."""
    # GIVEN a sample sheet object populated with samples
    assert novaseq_bcl2fastq_sample_sheet_object.lims_samples

    # WHEN converting to a sample sheet
    sample_sheet: str = novaseq_bcl2fastq_sample_sheet_object.construct_sample_sheet()

    # THEN assert a correctly formatted sample sheet was created
    sample_sheet_object: SampleSheet = validate_sample_sheet(
        sample_sheet_content=sample_sheet,
        bcl_converter=novaseq_bcl2fastq_sample_sheet_object.bcl_converter,
    )
    assert sample_sheet_object.samples


def test_construct_sample_sheet(sample_sheet_creator: SampleSheetCreator, project_dir: Path):
    """Test that a created bcl2fastq sample sheet has samples."""
    # GIVEN a sample sheet object populated with samples
    assert sample_sheet_creator.lims_samples

    # WHEN converting to a sample sheet
    sample_sheet_content: List[List[str]] = sample_sheet_creator.construct_sample_sheet()

    # THEN assert a correctly formatted sample sheet was created
    sample_sheet: SampleSheet = validate_sample_sheet(
        sample_sheet_content=sample_sheet_content,
    )
    assert sample_sheet.samples
