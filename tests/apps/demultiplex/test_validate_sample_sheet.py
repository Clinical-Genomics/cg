import logging
from typing import List, Dict

import pytest

from cg.apps.demultiplex.sample_sheet.models import SampleSheet, FlowCellSampleBcl2Fastq
from cg.apps.demultiplex.sample_sheet.validate import (
    get_raw_samples,
    validate_sample_sheet,
    get_samples_by_lane,
    validate_samples_are_unique,
)
from cg.constants.demultiplexing import BclConverter
from cg.exc import SampleSheetError


def test_validate_samples_are_unique(
    novaseq_sample_1: FlowCellSampleBcl2Fastq,
    novaseq_sample_2: FlowCellSampleBcl2Fastq,
):
    """Test that validating two different samples finishes successfully."""
    # GIVEN two different NovaSeq samples
    assert novaseq_sample_1 != novaseq_sample_2

    # WHEN validating the samples
    validate_samples_are_unique(samples=[novaseq_sample_1, novaseq_sample_2])

    # THEN no error is raised


def test_validate_samples_are_unique_not_unique(novaseq_sample_1: FlowCellSampleBcl2Fastq, caplog):
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
    novaseq_sample_1: FlowCellSampleBcl2Fastq,
    novaseq_sample_2: FlowCellSampleBcl2Fastq,
):
    """Test that grouping two samples with different lanes returns two groups."""
    # GIVEN two samples on two different lanes

    # WHEN getting the samples per lane
    samples_per_lane: Dict[int, List[FlowCellSampleBcl2Fastq]] = get_samples_by_lane(
        samples=[novaseq_sample_1, novaseq_sample_2]
    )

    # THEN the returned value is a dictionary
    assert isinstance(samples_per_lane, Dict)
    # THEN the dictionary has two entries
    assert len(samples_per_lane) == 2


def test_get_raw_samples_valid_sample_sheet(valid_sample_sheet_bcl2fastq: List[List[str]]):
    """Test that getting raw samples from a valid sample sheet gets a correct list of dictionaries."""
    # GIVEN a valid sample sheet

    # WHEN getting the list of raw samples from it
    raw_samples: List[Dict[str, str]] = get_raw_samples(
        sample_sheet_content=valid_sample_sheet_bcl2fastq
    )

    # THEN it returns a list with 2 dictionaries
    assert len(raw_samples) == 2
    # THEN the list contains dictionaries
    assert isinstance(raw_samples[0], Dict)
    # THEN the sample contains the key "Lane"
    assert "Lane" in raw_samples[0].keys()


def test_get_raw_samples_no_header(sample_sheet_samples_no_header: List[List[str]], caplog):
    """Test that getting samples from a sample sheet without header fails."""
    # GIVEN a sample sheet without header
    caplog.set_level(logging.INFO)

    # WHEN trying to get the samples from the sample sheet
    with pytest.raises(SampleSheetError):
        get_raw_samples(sample_sheet_content=sample_sheet_samples_no_header)

    # THEN an exception is raised because of the missing header
    assert "Could not find header in sample sheet" in caplog.text


def test_get_raw_samples_no_samples(sample_sheet_bcl2fastq_data_header: List[List[str]], caplog):
    """Test that getting samples from a sample sheet without samples fails."""
    # GIVEN a sample sheet without samples
    caplog.set_level(logging.INFO)

    # WHEN trying to get the samples from the sample sheet
    with pytest.raises(SampleSheetError):
        get_raw_samples(sample_sheet_content=sample_sheet_bcl2fastq_data_header)

    # THEN an exception is raised because of the missing samples
    assert "Could not find any samples in sample sheet" in caplog.text


def test_get_sample_sheet_s2_bcl2fastq_duplicate_same_lane(
    sample_sheet_bcl2fastq_duplicate_same_lane: List[List[str]],
):
    """Test that creating a Bcl2fastq sample sheet with duplicated samples in a lane fails."""
    # GIVEN a Bcl2fastq sample sheet with a sample duplicated in a lane

    # WHEN creating the sample sheet object
    with pytest.raises(SampleSheetError):
        # THEN a sample sheet error is raised
        validate_sample_sheet(
            sample_sheet_content=sample_sheet_bcl2fastq_duplicate_same_lane,
            bcl_converter=BclConverter.BCL2FASTQ,
        )


def test_get_sample_sheet_s2_dragen_duplicate_same_lane(
    sample_sheet_dragen_duplicate_same_lane: List[List[str]],
):
    """Test that creating a Dragen sample sheet with duplicated samples in a lane fails."""
    # GIVEN a Dragen sample sheet with a sample duplicated in a lane

    # WHEN creating the sample sheet object
    with pytest.raises(SampleSheetError):
        # THEN a sample sheet error is raised
        validate_sample_sheet(
            sample_sheet_content=sample_sheet_dragen_duplicate_same_lane,
            bcl_converter=BclConverter.DRAGEN,
        )


def test_get_sample_sheet_s2_bcl2fastq_duplicate_different_lanes(
    sample_sheet_bcl2fastq_duplicate_different_lane: List[List[str]],
):
    """Test that Bcl2fastq a sample sheet created with duplicated samples in different lanes has samples."""
    # GIVEN a Bcl2fastq sample sheet with same sample duplicated in different lanes

    # WHEN creating the sample sheet object
    sample_sheet: SampleSheet = validate_sample_sheet(
        sample_sheet_content=sample_sheet_bcl2fastq_duplicate_different_lane,
        bcl_converter=BclConverter.BCL2FASTQ,
    )

    # THEN a sample sheet is returned with samples in it
    assert sample_sheet.samples


def test_get_sample_sheet_s2_dragen_duplicate_different_lanes(
    sample_sheet_dragen_duplicate_different_lane: List[List[str]],
):
    """Test that Dragen a sample sheet created with duplicated samples in different lanes has samples."""
    # GIVEN a Dragen sample sheet with same sample duplicated in different lanes

    # WHEN creating the sample sheet object
    sample_sheet: SampleSheet = validate_sample_sheet(
        sample_sheet_content=sample_sheet_dragen_duplicate_different_lane,
        bcl_converter=BclConverter.DRAGEN,
    )

    # THEN a sample sheet is returned with samples in it
    assert sample_sheet.samples
