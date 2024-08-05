import logging

import pytest

from cg.apps.demultiplex.sample_sheet.read_sample_sheet import (
    get_raw_samples_from_content,
    get_samples_by_lane,
    validate_samples_are_unique,
)
from cg.apps.demultiplex.sample_sheet.sample_models import IlluminaSampleIndexSetting
from cg.exc import SampleSheetContentError, SampleSheetFormatError


def test_validate_samples_are_unique(
    novaseq6000_flow_cell_sample_1: IlluminaSampleIndexSetting,
    novaseq6000_flow_cell_sample_2: IlluminaSampleIndexSetting,
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
    novaseq6000_flow_cell_sample_1: IlluminaSampleIndexSetting, caplog
):
    """Test that validating two identical samples fails."""
    # GIVEN two identical NovaSeq samples
    caplog.set_level(logging.INFO)

    # WHEN validating the samples
    with pytest.raises(SampleSheetContentError):
        validate_samples_are_unique(
            samples=[novaseq6000_flow_cell_sample_1, novaseq6000_flow_cell_sample_1]
        )

    # THEN a sample sheet error is raised due to the samples being identical
    assert (
        f"Sample {novaseq6000_flow_cell_sample_1.sample_id} exists multiple times in sample sheet"
        in caplog.text
    )


def test_get_samples_by_lane(
    novaseq6000_flow_cell_sample_1: IlluminaSampleIndexSetting,
    novaseq6000_flow_cell_sample_2: IlluminaSampleIndexSetting,
):
    """Test that grouping two samples with different lanes returns two groups."""
    # GIVEN two samples on two different lanes

    # WHEN getting the samples per lane
    samples_per_lane: dict[int, list[IlluminaSampleIndexSetting]] = get_samples_by_lane(
        samples=[novaseq6000_flow_cell_sample_1, novaseq6000_flow_cell_sample_2]
    )

    # THEN the returned value is a dictionary
    assert isinstance(samples_per_lane, dict)
    # THEN the dictionary has two entries
    assert len(samples_per_lane) == 2


def test_get_raw_samples_valid_sample_sheet(
    hiseq_x_single_index_sample_sheet_content: list[list[str]],
):
    """Test that getting raw samples from a valid sample sheet gets a correct list of dictionaries."""
    # GIVEN a valid sample sheet

    # WHEN getting the list of raw samples from it
    raw_samples: list[dict[str, str]] = get_raw_samples_from_content(
        sample_sheet_content=hiseq_x_single_index_sample_sheet_content
    )

    # THEN it returns a list with 2 dictionaries
    assert len(raw_samples) == 9
    # THEN the list contains dictionaries
    assert isinstance(raw_samples[0], dict)
    # THEN the sample contains the key "Lane"
    assert "Lane" in raw_samples[0].keys()


def test_get_raw_samples_no_header(sample_sheet_samples_no_column_names: list[list[str]], caplog):
    """Test that getting samples from a sample sheet without header fails."""
    # GIVEN a sample sheet without header
    caplog.set_level(logging.INFO)

    # WHEN trying to get the samples from the sample sheet
    with pytest.raises(SampleSheetFormatError):
        get_raw_samples_from_content(sample_sheet_content=sample_sheet_samples_no_column_names)

    # THEN an exception is raised because of the missing header
    assert "Could not find header in sample sheet" in caplog.text


def test_get_raw_samples_no_samples(sample_sheet_bcl_convert_data_header: list[list[str]], caplog):
    """Test that getting samples from a sample sheet without samples fails."""
    # GIVEN a sample sheet without samples
    caplog.set_level(logging.INFO)

    # WHEN trying to get the samples from the sample sheet
    with pytest.raises(SampleSheetFormatError):
        get_raw_samples_from_content(sample_sheet_content=sample_sheet_bcl_convert_data_header)

    # THEN an exception is raised because of the missing samples
    assert "Could not find any samples in sample sheet" in caplog.text
