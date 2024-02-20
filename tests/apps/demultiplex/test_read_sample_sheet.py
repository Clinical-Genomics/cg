import logging
from pathlib import Path
from typing import Type

import pytest

from cg.apps.demultiplex.sample_sheet.read_sample_sheet import (
    get_raw_samples_from_content,
    get_sample_type_from_content,
    get_samples_by_lane,
    validate_samples_are_unique,
)
from cg.apps.demultiplex.sample_sheet.sample_models import (
    FlowCellSample,
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.constants.constants import FileFormat
from cg.exc import SampleSheetError
from cg.io.controller import ReadFile


def test_validate_samples_are_unique(
    novaseq6000_flow_cell_sample_1: FlowCellSampleBcl2Fastq,
    novaseq6000_flow_cell_sample_2: FlowCellSampleBcl2Fastq,
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
    novaseq6000_flow_cell_sample_1: FlowCellSampleBcl2Fastq, caplog
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


def test_get_samples_by_lane(
    novaseq6000_flow_cell_sample_1: FlowCellSampleBcl2Fastq,
    novaseq6000_flow_cell_sample_2: FlowCellSampleBcl2Fastq,
):
    """Test that grouping two samples with different lanes returns two groups."""
    # GIVEN two samples on two different lanes

    # WHEN getting the samples per lane
    samples_per_lane: dict[int, list[FlowCellSample]] = get_samples_by_lane(
        samples=[novaseq6000_flow_cell_sample_1, novaseq6000_flow_cell_sample_2]
    )

    # THEN the returned value is a dictionary
    assert isinstance(samples_per_lane, dict)
    # THEN the dictionary has two entries
    assert len(samples_per_lane) == 2


def test_get_raw_samples_valid_sample_sheet(valid_sample_sheet_bcl2fastq: list[list[str]]):
    """Test that getting raw samples from a valid sample sheet gets a correct list of dictionaries."""
    # GIVEN a valid sample sheet

    # WHEN getting the list of raw samples from it
    raw_samples: list[dict[str, str]] = get_raw_samples_from_content(
        sample_sheet_content=valid_sample_sheet_bcl2fastq
    )

    # THEN it returns a list with 2 dictionaries
    assert len(raw_samples) == 2
    # THEN the list contains dictionaries
    assert isinstance(raw_samples[0], dict)
    # THEN the sample contains the key "Lane"
    assert "Lane" in raw_samples[0].keys()


def test_get_raw_samples_no_header(sample_sheet_samples_no_header: list[list[str]], caplog):
    """Test that getting samples from a sample sheet without header fails."""
    # GIVEN a sample sheet without header
    caplog.set_level(logging.INFO)

    # WHEN trying to get the samples from the sample sheet
    with pytest.raises(SampleSheetError):
        get_raw_samples_from_content(sample_sheet_content=sample_sheet_samples_no_header)

    # THEN an exception is raised because of the missing header
    assert "Could not find header in sample sheet" in caplog.text


def test_get_raw_samples_no_samples(sample_sheet_bcl2fastq_data_header: list[list[str]], caplog):
    """Test that getting samples from a sample sheet without samples fails."""
    # GIVEN a sample sheet without samples
    caplog.set_level(logging.INFO)

    # WHEN trying to get the samples from the sample sheet
    with pytest.raises(SampleSheetError):
        get_raw_samples_from_content(sample_sheet_content=sample_sheet_bcl2fastq_data_header)

    # THEN an exception is raised because of the missing samples
    assert "Could not find any samples in sample sheet" in caplog.text


def test_get_sample_type_for_bcl_convert(bcl_convert_sample_sheet_path: Path):
    # GIVEN a bcl convert sample sheet path

    # WHEN getting the sample type
    content: list[list[str]] = ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=bcl_convert_sample_sheet_path
    )
    sample_type: Type[FlowCellSample] = get_sample_type_from_content(content)

    # THEN the sample type is FlowCellSampleBCLConvert
    assert sample_type is FlowCellSampleBCLConvert


def test_get_sample_type_for_bcl2fastq(bcl2fastq_sample_sheet_path: Path):
    # GIVEN a bcl convert sample sheet path

    # WHEN getting the sample type
    content: list[list[str]] = ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=bcl2fastq_sample_sheet_path
    )
    sample_type: Type[FlowCellSample] = get_sample_type_from_content(content)

    # THEN the sample type is FlowCellSampleBCLConvert
    assert sample_type is FlowCellSampleBcl2Fastq


def test_validate_sample_sheet_bcl2fastq_duplicate_same_lane(
    sample_sheet_bcl2fastq_duplicate_same_lane: list[list[str]],
):
    """Test that creating a Bcl2fastq sample sheet with duplicated samples in a lane fails."""
    # GIVEN a Bcl2fastq sample sheet with a sample duplicated in a lane

    # WHEN creating the sample sheet object

    # THEN a sample sheet error is raised


def test_validate_sample_sheet_bcl2fastq_duplicate_different_lanes(
    sample_sheet_bcl2fastq_duplicate_different_lane: list[list[str]],
):
    """Test that Bcl2fastq a sample sheet created with duplicated samples in different lanes has samples."""
    # GIVEN a Bcl2fastq sample sheet with same sample duplicated in different lanes

    # WHEN creating the sample sheet object

    # THEN a sample sheet is returned with samples in it
