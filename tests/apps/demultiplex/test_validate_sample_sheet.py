import logging
from pathlib import Path
from typing import List, Dict

import pytest

from cg.apps.demultiplex.sample_sheet.models import SampleSheet, NovaSeqSample
from cg.apps.demultiplex.sample_sheet.validate import (
    get_raw_samples,
    get_sample_sheet,
    get_sample_sheet_from_file,
    get_samples_by_lane,
    validate_samples_are_unique,
)
from cg.exc import SampleSheetError


def test_validate_samples_are_unique(
    novaseq_sample_1: NovaSeqSample,
    novaseq_sample_2: NovaSeqSample,
):
    """Test that validating two different samples finishes successfully."""
    # GIVEN two different NovaSeq samples
    assert novaseq_sample_1 != novaseq_sample_2

    # WHEN validating the samples
    validate_samples_are_unique(samples=[novaseq_sample_1, novaseq_sample_2])

    # THEN no error is raised


def test_validate_samples_are_unique_not_unique(novaseq_sample_1: NovaSeqSample, caplog):
    """Test that validating two identical samples fails."""
    # GIVEN two identical NovaSeq samples
    caplog.set_level(logging.INFO)

    # WHEN validating the samples
    with pytest.raises(SampleSheetError):
        validate_samples_are_unique(samples=[novaseq_sample_1, novaseq_sample_1])

    # THEN a sample sheet error is raised due to the samples being identical
    assert (
        f"Sample {novaseq_sample_1.sample_id} exists multiple times in sample sheet" in caplog.text
    )


def test_get_samples_by_lane(
    novaseq_sample_1: NovaSeqSample,
    novaseq_sample_2: NovaSeqSample,
):
    """Test that grouping two samples with different lanes returns two groups."""
    # GIVEN two samples on two different lanes

    # WHEN getting the samples per lane
    samples_per_lane: Dict[int, List[NovaSeqSample]] = get_samples_by_lane(
        samples=[novaseq_sample_1, novaseq_sample_2]
    )

    # THEN the returned value is a dictionary
    assert isinstance(samples_per_lane, Dict)
    # THEN the dictionary has two entries
    assert len(samples_per_lane) == 2


def test_get_raw_samples_valid_sample_sheet(valid_sample_sheet_bcl2fastq: str):
    """Test that getting raw samples from a valid sample sheet gets a correct list of dictionaries."""
    # GIVEN a valid sample sheet

    # WHEN getting the list of raw samples from it
    raw_samples: List[Dict[str, str]] = get_raw_samples(sample_sheet=valid_sample_sheet_bcl2fastq)

    # THEN it returns a list with 2 dictionaries
    assert len(raw_samples) == 2
    # THEN the list contains dictionaries
    assert isinstance(raw_samples[0], Dict)
    # THEN the sample contains the key "Lane"
    assert "Lane" in raw_samples[0].keys()


def test_get_raw_samples_no_header(sample_sheet_samples_no_header: str, caplog):
    """Test that getting samples from a sample sheet without header fails."""
    # GIVEN a sample sheet without header
    caplog.set_level(logging.INFO)

    # WHEN trying to get the samples from the sample sheet
    with pytest.raises(SampleSheetError):
        get_raw_samples(sample_sheet=sample_sheet_samples_no_header)

    # THEN an exception is raised because of the missing header
    assert "Could not find header in sample sheet" in caplog.text


def test_get_raw_samples_no_samples(sample_sheet_bcl2fastq_data_header: str, caplog):
    """Test that getting samples from a sample sheet without samples fails."""
    # GIVEN a sample sheet without samples
    caplog.set_level(logging.INFO)

    # WHEN trying to get the samples from the sample sheet
    with pytest.raises(SampleSheetError):
        get_raw_samples(sample_sheet=sample_sheet_bcl2fastq_data_header)

    # THEN an exception is raised because of the missing samples
    assert "Could not find any samples in sample sheet" in caplog.text


def test_get_sample_sheet_s2_bcl2fastq(
    valid_sample_sheet_bcl2fastq: str,
):
    """Test that a bcl2fastq sample sheet created from valid parameters has the correct type."""
    # GIVEN a valid sample sheet to be used with bcl2fastq

    # WHEN creating the sample sheet object from a string
    sheet: SampleSheet = get_sample_sheet(
        sample_sheet=valid_sample_sheet_bcl2fastq,
        sheet_type="S2",
        bcl_converter="bcl2fastq",
    )
    # THEN it has the correct type
    assert sheet.type == "S2"


def test_get_sample_sheet_s2_dragen(
    valid_sample_sheet_dragen: str,
):
    """Test that a dragen sample sheet created from valid parameters has the correct type."""
    # GIVEN a valid sample sheet to be used with dragen

    # WHEN creating the sample sheet object from a string
    sheet: SampleSheet = get_sample_sheet(
        sample_sheet=valid_sample_sheet_dragen,
        sheet_type="S2",
        bcl_converter="dragen",
    )
    # THEN it has the correct type
    assert sheet.type == "S2"


def test_get_sample_sheet_s2_bcl2fastq_duplicate_same_lane(
    sample_sheet_bcl2fastq_duplicate_same_lane: str,
):
    """Test that creating a bcl2fastq sample sheet with duplicated samples in a lane fails."""
    # GIVEN a bcl2fastq sample sheet with a sample duplicated in a lane

    # WHEN creating the sample sheet object
    with pytest.raises(SampleSheetError):
        # THEN a sample sheet error is raised
        get_sample_sheet(
            sample_sheet=sample_sheet_bcl2fastq_duplicate_same_lane,
            sheet_type="S2",
            bcl_converter="bcl2fastq",
        )


def test_get_sample_sheet_s2_dragen_duplicate_same_lane(
    sample_sheet_dragen_duplicate_same_lane: str,
):
    """Test that creating a dragen sample sheet with duplicated samples in a lane fails."""
    # GIVEN a dragen sample sheet with a sample duplicated in a lane

    # WHEN creating the sample sheet object
    with pytest.raises(SampleSheetError):
        # THEN a sample sheet error is raised
        get_sample_sheet(
            sample_sheet=sample_sheet_dragen_duplicate_same_lane,
            sheet_type="S2",
            bcl_converter="dragen",
        )


def test_get_sample_sheet_s2_bcl2fastq_duplicate_different_lanes(
    sample_sheet_bcl2fastq_duplicate_different_lane: str,
):
    """Test that bcl2fastq a sample sheet created with duplicated samples in different lanes has samples."""
    # GIVEN a bcl2fastq sample sheet with same sample duplicated in different lanes

    # WHEN creating the sample sheet object
    sample_sheet: SampleSheet = get_sample_sheet(
        sample_sheet=sample_sheet_bcl2fastq_duplicate_different_lane,
        sheet_type="S2",
        bcl_converter="bcl2fastq",
    )

    # THEN a sample sheet is returned with samples in it
    assert sample_sheet.samples


def test_get_sample_sheet_s2_dragen_duplicate_different_lanes(
    sample_sheet_dragen_duplicate_different_lane: str,
):
    """Test that dragen a sample sheet created with duplicated samples in different lanes has samples."""
    # GIVEN a dragen sample sheet with same sample duplicated in different lanes

    # WHEN creating the sample sheet object
    sample_sheet: SampleSheet = get_sample_sheet(
        sample_sheet=sample_sheet_dragen_duplicate_different_lane,
        sheet_type="S2",
        bcl_converter="dragen",
    )

    # THEN a sample sheet is returned with samples in it
    assert sample_sheet.samples


def test_get_sample_sheet_from_file_s2_bcl2fastq(
    valid_sample_sheet_bcl2fastq_path: Path,
):
    """Test that a bcl2fastq sample sheet created from a file has the correct type."""
    # GIVEN a bcl2fastq sample sheet file path

    # WHEN creating the sample sheet object
    sheet: SampleSheet = get_sample_sheet_from_file(
        infile=valid_sample_sheet_bcl2fastq_path,
        sheet_type="S2",
        bcl_converter="bcl2fastq",
    )

    # THEN the sample sheet has the correct type
    assert sheet.type == "S2"


def test_get_sample_sheet_from_file_s2_dragen(
    valid_sample_sheet_dragen_path: Path,
):
    """Test that a dragen sample sheet created from a file has the correct type."""
    # GIVEN a dragen sample sheet file path

    # WHEN creating the sample sheet
    sheet: SampleSheet = get_sample_sheet_from_file(
        infile=valid_sample_sheet_dragen_path,
        sheet_type="S2",
        bcl_converter="dragen",
    )

    # THEN the sample sheet has the correct type
    assert sheet.type == "S2"
