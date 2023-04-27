from pathlib import Path

import pytest

from cg.apps.demultiplex.sample_sheet.base import SampleSheet, SampleSheetError
from cg.apps.demultiplex.sample_sheet.validate import get_sample_sheet, get_sample_sheet_from_file


def test_get_sample_sheet_s2_bcl2fastq(
    valid_bcl2fastq_sample_sheet_str: str,
    s2_sample_sheet_type: str,
    bcl2fastq_converter: str,
):
    """Test that a bcl2fastq sample sheet created from valid parameters has the correct type."""
    # GIVEN a valid sample sheet to be used with bcl2fastq

    # WHEN creating the sample sheet object from a string
    sheet: SampleSheet = get_sample_sheet(
        sample_sheet=valid_bcl2fastq_sample_sheet_str,
        sheet_type=s2_sample_sheet_type,
        bcl_converter=bcl2fastq_converter,
    )
    # THEN it has the correct type
    assert sheet.type == s2_sample_sheet_type


def test_get_sample_sheet_s2_dragen(
    valid_dragen_sample_sheet_str: str,
    s2_sample_sheet_type: str,
    dragen_converter: str,
):
    """Test that a dragen sample sheet created from valid parameters has the correct type."""
    # GIVEN a valid sample sheet to be used with dragen

    # WHEN creating the sample sheet object from a string
    sheet: SampleSheet = get_sample_sheet(
        sample_sheet=valid_dragen_sample_sheet_str,
        sheet_type=s2_sample_sheet_type,
        bcl_converter=dragen_converter,
    )
    # THEN it has the correct type
    assert sheet.type == s2_sample_sheet_type


def test_get_sample_sheet_s2_bcl2fastq_duplicate_same_lane(
    bcl2fastq_sample_sheet_duplicate_same_lane_str: str,
    s2_sample_sheet_type: str,
    bcl2fastq_converter: str,
):
    """Test that creating a bcl2fastq sample sheet with duplicated samples in a lane fails."""
    # GIVEN a bcl2fastq sample sheet with a sample duplicated in a lane

    # WHEN creating the sample sheet object
    with pytest.raises(SampleSheetError):
        # THEN a sample sheet error is raised
        get_sample_sheet(
            sample_sheet=bcl2fastq_sample_sheet_duplicate_same_lane_str,
            sheet_type=s2_sample_sheet_type,
            bcl_converter=bcl2fastq_converter,
        )


def test_get_sample_sheet_s2_dragen_duplicate_same_lane(
    dragen_sample_sheet_duplicate_same_lane_str: str,
    s2_sample_sheet_type: str,
    dragen_converter: str,
):
    """Test that creating a dragen sample sheet with duplicated samples in a lane fails."""
    # GIVEN a dragen sample sheet with a sample duplicated in a lane

    # WHEN creating the sample sheet object
    with pytest.raises(SampleSheetError):
        # THEN a sample sheet error is raised
        get_sample_sheet(
            sample_sheet=dragen_sample_sheet_duplicate_same_lane_str,
            sheet_type=s2_sample_sheet_type,
            bcl_converter=dragen_converter,
        )


def test_get_sample_sheet_s2_bcl2fastq_duplicate_different_lanes(
    bcl2fastq_sample_sheet_duplicate_different_lane_str: str,
    s2_sample_sheet_type: str,
    bcl2fastq_converter: str,
):
    """Test that bcl2fastq a sample sheet created with duplicated samples in different lanes has samples."""
    # GIVEN a bcl2fastq sample sheet with same sample duplicated in different lanes

    # WHEN creating the sample sheet object
    sample_sheet: SampleSheet = get_sample_sheet(
        sample_sheet=bcl2fastq_sample_sheet_duplicate_different_lane_str,
        sheet_type=s2_sample_sheet_type,
        bcl_converter=bcl2fastq_converter,
    )

    # THEN a sample sheet is returned with samples in it
    assert sample_sheet.samples


def test_get_sample_sheet_s2_dragen_duplicate_different_lanes(
    dragen_sample_sheet_duplicate_different_lane_str: str,
    s2_sample_sheet_type: str,
    dragen_converter: str,
):
    """Test that dragen a sample sheet created with duplicated samples in different lanes has samples."""
    # GIVEN a dragen sample sheet with same sample duplicated in different lanes

    # WHEN creating the sample sheet object
    sample_sheet: SampleSheet = get_sample_sheet(
        sample_sheet=dragen_sample_sheet_duplicate_different_lane_str,
        sheet_type=s2_sample_sheet_type,
        bcl_converter=dragen_converter,
    )

    # THEN a sample sheet is returned with samples in it
    assert sample_sheet.samples


def test_get_sample_sheet_s2_bcl2fastq_missing_header(
    sample_sheet_no_sample_header_str: str,
    s2_sample_sheet_type: str,
    bcl2fastq_converter: str,
):
    """Test that creating a bcl2fastq sample sheet without a sample header fails."""
    # GIVEN a sample sheet with a missing sample header

    # WHEN creating the sample sheet object using the bcl2fastq converter
    with pytest.raises(SampleSheetError):
        # THEN a sample sheet error is raised
        get_sample_sheet(
            sample_sheet=sample_sheet_no_sample_header_str,
            sheet_type=s2_sample_sheet_type,
            bcl_converter=bcl2fastq_converter,
        )


def test_get_sample_sheet_s2_dragen_missing_header(
    sample_sheet_no_sample_header_str: str,
    s2_sample_sheet_type: str,
    dragen_converter: str,
):
    """Test that creating a dragen sample sheet without a sample header fails."""
    # GIVEN a sample sheet with a missing sample header

    # WHEN creating the sample sheet object using the dragen converter
    with pytest.raises(SampleSheetError):
        # THEN a sample sheet error is raised
        get_sample_sheet(
            sample_sheet=sample_sheet_no_sample_header_str,
            sheet_type=s2_sample_sheet_type,
            bcl_converter=dragen_converter,
        )


def test_get_sample_sheet_s2_bcl2fastq_missing_samples(
    bcl2fastq_sample_sheet_no_samples: str, s2_sample_sheet_type, bcl2fastq_converter: str
):
    """Test that creating a bcl2fastq sample sheet without samples fails."""
    # GIVEN a bcl2fastq sample sheet without samples

    # WHEN creating the sample sheet object
    with pytest.raises(SampleSheetError):
        # THEN a sample sheet error is raised
        get_sample_sheet(
            sample_sheet=bcl2fastq_sample_sheet_no_samples,
            sheet_type=s2_sample_sheet_type,
            bcl_converter=bcl2fastq_converter,
        )


def test_get_sample_sheet_s2_dragen_missing_samples(
    dragen_sample_sheet_no_samples: str, s2_sample_sheet_type, dragen_converter: str
):
    """Test that creating a dragen sample sheet without samples fails."""
    # GIVEN a dragen sample sheet without samples

    # WHEN creating the sample sheet object
    with pytest.raises(SampleSheetError):
        # THEN a sample sheet error is raised
        get_sample_sheet(
            sample_sheet=dragen_sample_sheet_no_samples,
            sheet_type=s2_sample_sheet_type,
            bcl_converter=dragen_converter,
        )


def test_get_sample_sheet_from_file_s2_bcl2fastq(
    valid_s2_sheet_bcl2fastq_path: Path, s2_sample_sheet_type: str, bcl2fastq_converter: str
):
    """Test that a bcl2fastq sample sheet created from a file has the correct type."""
    # GIVEN a bcl2fastq sample sheet file path

    # WHEN creating the sample sheet object
    sheet: SampleSheet = get_sample_sheet_from_file(
        infile=valid_s2_sheet_bcl2fastq_path,
        sheet_type=s2_sample_sheet_type,
        bcl_converter=bcl2fastq_converter,
    )

    # THEN the sample sheet has the correct type
    assert sheet.type == s2_sample_sheet_type


def test_get_sample_sheet_from_file_s2_dragen(
    valid_s2_sheet_dragen_path: Path, s2_sample_sheet_type: str, dragen_converter: str
):
    """Test that a dragen sample sheet created from a file has the correct type."""
    # GIVEN a dragen sample sheet file path

    # WHEN creating the sample sheet
    sheet: SampleSheet = get_sample_sheet_from_file(
        infile=valid_s2_sheet_dragen_path,
        sheet_type=s2_sample_sheet_type,
        bcl_converter=dragen_converter,
    )

    # THEN the sample sheet has the correct type
    assert sheet.type == s2_sample_sheet_type
