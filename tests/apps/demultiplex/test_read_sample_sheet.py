import logging
from typing import List, Dict, Type
import pytest
from pathlib import Path
from cg.exc import SampleSheetError
from cg.apps.demultiplex.sample_sheet.models import (
    SampleSheet,
    FlowCellSample,
    FlowCellSampleNovaSeq6000Bcl2Fastq,
    FlowCellSampleNovaSeq6000Dragen,
)
from cg.apps.demultiplex.sample_sheet.read_sample_sheet import (
    validate_samples_are_unique,
    is_valid_sample_internal_id,
    get_samples_by_lane,
    get_sample_internal_ids_from_sample_sheet,
    get_validated_sample_sheet,
    get_raw_samples,
)


def test_validate_samples_are_unique(
    novaseq6000_flow_cell_sample_1: FlowCellSampleNovaSeq6000Bcl2Fastq,
    novaseq6000_flow_cell_sample_2: FlowCellSampleNovaSeq6000Bcl2Fastq,
):
    """Test that validating two different samples finishes successfully."""
    # GIVEN two different NovaSeq samples
    assert novaseq6000_flow_cell_sample_1 != novaseq6000_flow_cell_sample_2

    # WHEN validating the samples
    validate_samples_are_unique(
        samples=[novaseq6000_flow_cell_sample_1, novaseq6000_flow_cell_sample_2]
    )

    # THEN no error is raised


def test_validate_samples_are_unique_when_not_unique(
    novaseq6000_flow_cell_sample_1: FlowCellSampleNovaSeq6000Bcl2Fastq, caplog
):
    """Test that validating two identical samples fails."""
    # GIVEN two identical NovaSeq samples
    caplog.set_level(logging.INFO)

    # WHEN validating the samples
    with pytest.raises(SampleSheetError):
        validate_samples_are_unique(
            samples=[novaseq6000_flow_cell_sample_1, novaseq6000_flow_cell_sample_1]
        )

    # THEN a sample sheet error is raised due to the samples being identical
    assert (
        f"Sample {novaseq6000_flow_cell_sample_1.sample_id} exists multiple times in sample sheet"
        in caplog.text
    )


def test_is_valid_sample_internal_id(
    novaseq6000_flow_cell_sample_1: FlowCellSampleNovaSeq6000Bcl2Fastq,
    novaseq6000_flow_cell_sample_2: FlowCellSampleNovaSeq6000Bcl2Fastq,
):
    """Test that validating two different samples finishes successfully."""
    # GIVEN two different NovaSeq samples with valid internal IDs

    # WHEN validating the sample internal ids
    for sample in [novaseq6000_flow_cell_sample_1, novaseq6000_flow_cell_sample_2]:
        # THEN no error is raised
        assert is_valid_sample_internal_id(sample_internal_id=sample.sample_id)


def test_is_valid_sample_internal_id_invalid_sample_internal_ids(
    novaseq6000_flow_cell_sample_1: FlowCellSampleNovaSeq6000Bcl2Fastq,
    novaseq6000_flow_cell_sample_2: FlowCellSampleNovaSeq6000Bcl2Fastq,
):
    """Test that validating two different samples finishes successfully."""
    # GIVEN two different NovaSeq samples with valid internal IDs

    # WHEN setting the sample internal ids to invalid values
    novaseq6000_flow_cell_sample_1.sample_id = "invalid_sample_id"
    novaseq6000_flow_cell_sample_2.sample_id = "invalid_sample_id"

    # WHEN validating the sample internal ids
    # THEN no error is raised
    for sample in [novaseq6000_flow_cell_sample_1, novaseq6000_flow_cell_sample_2]:
        assert not is_valid_sample_internal_id(sample_internal_id=sample.sample_id)


def test_get_samples_by_lane(
    novaseq6000_flow_cell_sample_1: FlowCellSampleNovaSeq6000Bcl2Fastq,
    novaseq6000_flow_cell_sample_2: FlowCellSampleNovaSeq6000Bcl2Fastq,
):
    """Test that grouping two samples with different lanes returns two groups."""
    # GIVEN two samples on two different lanes

    # WHEN getting the samples per lane
    samples_per_lane: Dict[int, List[FlowCellSample]] = get_samples_by_lane(
        samples=[novaseq6000_flow_cell_sample_1, novaseq6000_flow_cell_sample_2]
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


def test_get_sample_sheet_bcl2fastq_duplicate_same_lane(
    sample_sheet_bcl2fastq_duplicate_same_lane: List[List[str]],
):
    """Test that creating a Bcl2fastq sample sheet with duplicated samples in a lane fails."""
    # GIVEN a Bcl2fastq sample sheet with a sample duplicated in a lane

    # WHEN creating the sample sheet object
    with pytest.raises(SampleSheetError):
        # THEN a sample sheet error is raised
        get_validated_sample_sheet(
            sample_sheet_content=sample_sheet_bcl2fastq_duplicate_same_lane,
            sample_type=FlowCellSampleNovaSeq6000Bcl2Fastq,
        )


def test_get_sample_sheet_dragen_duplicate_same_lane(
    sample_sheet_dragen_duplicate_same_lane: List[List[str]],
):
    """Test that creating a Dragen sample sheet with duplicated samples in a lane fails."""
    # GIVEN a Dragen sample sheet with a sample duplicated in a lane

    # WHEN creating the sample sheet object
    with pytest.raises(SampleSheetError):
        # THEN a sample sheet error is raised
        get_validated_sample_sheet(
            sample_sheet_content=sample_sheet_dragen_duplicate_same_lane,
            sample_type=FlowCellSampleNovaSeq6000Dragen,
        )


def test_get_sample_sheet_bcl2fastq_duplicate_different_lanes(
    sample_sheet_bcl2fastq_duplicate_different_lane: List[List[str]],
):
    """Test that Bcl2fastq a sample sheet created with duplicated samples in different lanes has samples."""
    # GIVEN a Bcl2fastq sample sheet with same sample duplicated in different lanes

    # WHEN creating the sample sheet object
    sample_sheet: SampleSheet = get_validated_sample_sheet(
        sample_sheet_content=sample_sheet_bcl2fastq_duplicate_different_lane,
        sample_type=FlowCellSampleNovaSeq6000Bcl2Fastq,
    )

    # THEN a sample sheet is returned with samples in it
    assert sample_sheet.samples


def test_get_sample_sheet_dragen_duplicate_different_lanes(
    sample_sheet_dragen_duplicate_different_lane: List[List[str]],
):
    """Test that Dragen a sample sheet created with duplicated samples in different lanes has samples."""
    # GIVEN a Dragen sample sheet with same sample duplicated in different lanes

    # WHEN creating the sample sheet object
    sample_sheet: SampleSheet = get_validated_sample_sheet(
        sample_sheet_content=sample_sheet_dragen_duplicate_different_lane,
        sample_type=FlowCellSampleNovaSeq6000Dragen,
    )

    # THEN a sample sheet is returned with samples in it
    assert sample_sheet.samples


def test_get_sample_internal_ids_from_sample_sheet(
    novaseq6000_bcl_convert_sample_sheet_path: Path,
    flow_cell_type: Type[FlowCellSample] = FlowCellSampleNovaSeq6000Dragen,
):
    """Test that getting sample internal ids from a sample sheet returns a unique list of strings."""
    # GIVEN a path to a sample sheet with only valid samples

    # WHEN getting the valid sample internal ids
    sample_internal_ids: List[str] = get_sample_internal_ids_from_sample_sheet(
        sample_sheet_path=novaseq6000_bcl_convert_sample_sheet_path,
        flow_cell_sample_type=flow_cell_type,
    )

    # THEN the returned value is a list
    assert isinstance(sample_internal_ids, List)
    # THEN the list contains strings
    assert isinstance(sample_internal_ids[0], str)
    # THEN the sample internal ids are unique
    assert len(sample_internal_ids) == len(set(sample_internal_ids))
    # THEN the sample internal ids are the expected ones
    for sample_internal_id in sample_internal_ids:
        assert is_valid_sample_internal_id(sample_internal_id=sample_internal_id) is True
