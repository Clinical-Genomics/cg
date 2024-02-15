from typing import Type

import pytest
from _pytest.fixtures import FixtureRequest

from cg.apps.demultiplex.sample_sheet.sample_models import (
    FlowCellSample,
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.apps.demultiplex.sample_sheet.sample_sheet_validator import SampleSheetValidator
from cg.constants.demultiplexing import SampleSheetBCLConvertSections
from cg.exc import SampleSheetError


@pytest.mark.parametrize(
    "sample_sheet_validator, expected_sample_type",
    [
        ("hiseq_x_single_index_sample_sheet_validator", FlowCellSampleBCLConvert),
        ("hiseq_x_single_index_bcl2fastq_sample_sheet_validator", FlowCellSampleBcl2Fastq),
    ],
)
def test_get_sample_type_correct_sample_sheet(
    sample_sheet_validator: str, expected_sample_type: Type[FlowCellSample], request: FixtureRequest
):
    """Test that the correct sample type is returned."""
    # GIVEN a sample sheet validator
    validator: SampleSheetValidator = request.getfixturevalue(sample_sheet_validator)

    # WHEN getting the sample type
    sample_type: Type = validator._get_sample_type()

    # THEN the correct sample type is returned
    assert sample_type == expected_sample_type


def test_get_sample_type_incorrect_sample_sheet(
    novaseq_x_sample_sheet_validator: SampleSheetValidator, caplog
):
    """Test that the correct sample type is returned."""
    # GIVEN the content of an invalid sample sheet
    novaseq_x_sample_sheet_validator.content = [["invalid", "content"], ["sample", "sheet"]]

    # WHEN getting the sample type
    with pytest.raises(SampleSheetError):
        # THEN a SampleSheetError is raised
        novaseq_x_sample_sheet_validator._get_sample_type()
    assert "Could not determine sample sheet type" in caplog.text


def test_validate_all_sections_present(
    novaseq_x_sample_sheet_validator: SampleSheetValidator,
    sample_sheet_content_only_headers: list[list[str]],
):
    """Test that when all sections are present in the sample sheet the validation passes."""
    # GIVEN a sample sheet content with all the required sections and a sample sheet validator
    novaseq_x_sample_sheet_validator.content = sample_sheet_content_only_headers
    assert len(novaseq_x_sample_sheet_validator.content) == 4

    # WHEN validating the sections of the sample sheet
    novaseq_x_sample_sheet_validator.validate_all_sections_present()

    # THEN no error is raised


def test_validate_all_sections_present_missing_section(
    novaseq_x_sample_sheet_validator: SampleSheetValidator,
    sample_sheet_content_missing_data_header: list[list[str]],
    caplog: pytest.LogCaptureFixture,
):
    """Test that when one sections is missing in the sample sheet the validation fails."""
    # GIVEN a sample sheet content with a missing section and a sample sheet validator
    novaseq_x_sample_sheet_validator.content = sample_sheet_content_missing_data_header
    assert len(novaseq_x_sample_sheet_validator.content) == 3

    # WHEN validating the sections of the sample sheet
    with pytest.raises(SampleSheetError):
        # THEN a SampleSheetError is raised
        novaseq_x_sample_sheet_validator.validate_all_sections_present()
    assert "Sample sheet does not have all the necessary sections" in caplog.text


@pytest.mark.parametrize(
    "sample_sheet_validator, expected_index_settings_name",
    [
        ("novaseq_6000_pre_1_5_kits_sample_sheet_validator", "NoReverseComplements"),
        ("novaseq_6000_post_1_5_kits_sample_sheet_validator", "NovaSeq6000Post1.5Kits"),
        ("novaseq_x_sample_sheet_validator", "NovaSeqX"),
    ],
    ids=["NovaSeq6000Pre1.5Kits", "NovaSeq6000Post1.5Kits", "NovaSeqX"],
)
def test_get_index_settings_name(
    sample_sheet_validator: str, expected_index_settings_name: str, request: FixtureRequest
):
    """Test that the correct index settings name is returned."""
    # GIVEN a sample sheet validator
    validator: SampleSheetValidator = request.getfixturevalue(sample_sheet_validator)

    # WHEN getting the index settings name
    index_settings_name: str = validator._get_index_settings_name()

    # THEN the correct index settings name is returned
    assert index_settings_name == expected_index_settings_name


def test_get_index_settings_name_missing_index_settings(
    novaseq_x_sample_sheet_validator: SampleSheetValidator, caplog
):
    """Test that getting the index settings from a sample sheet without it fails."""
    # GIVEN the content of a sample sheet without index settings
    novaseq_x_sample_sheet_validator.content.pop(5)
    assert (
        not [SampleSheetBCLConvertSections.Header.INDEX_SETTINGS.value, "NovaSeqX"]
        in novaseq_x_sample_sheet_validator.content
    )

    # WHEN getting the index settings name
    with pytest.raises(SampleSheetError):
        # THEN a SampleSheetError is raised
        novaseq_x_sample_sheet_validator._get_index_settings_name()
    assert "No index settings found in sample sheet" in caplog.text


@pytest.mark.parametrize(
    "sample_sheet_validator, expected_reverse_complement",
    [
        ("novaseq_6000_pre_1_5_kits_sample_sheet_validator", False),
        ("novaseq_6000_post_1_5_kits_sample_sheet_validator", False),
        ("novaseq_x_sample_sheet_validator", True),
    ],
    ids=["NovaSeq6000Pre1.5Kits", "NovaSeq6000Post1.5Kits", "NovaSeqX"],
)
def test_set_is_index2_reverse_complement(
    sample_sheet_validator: str, expected_reverse_complement: bool, request: FixtureRequest
):
    """Test that the correct value for index2 reverse complement value is set."""
    # GIVEN a sample sheet validator
    validator: SampleSheetValidator = request.getfixturevalue(sample_sheet_validator)

    # WHEN setting the index2 reverse complement value
    validator.set_is_index2_reverse_complement()

    # THEN the correct value is set
    assert validator.is_index2_reverse_complement == expected_reverse_complement


@pytest.mark.parametrize(
    "sample_sheet_content, nullable, expected",
    [
        ([[SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_2, 10]], False, 10),
        ([[SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_2, 10]], True, 10),
        ([["not_a_cycle", 10]], True, None),
    ],
    ids=["index2_cycles", "index2_cycles_nullable", "not_a_cycle_nullable"],
)
def test_get_cycle(
    sample_sheet_content: list[list[str]],
    nullable: bool,
    expected: int,
    novaseq_x_sample_sheet_validator: SampleSheetValidator,
):
    """Test that a cycle value is fetched when the content is correct."""
    # GIVEN a sample sheet validator with a modified sample sheet content
    novaseq_x_sample_sheet_validator.content = sample_sheet_content
    assert len(novaseq_x_sample_sheet_validator.content) == 1

    # WHEN fetching the cycle value
    result = novaseq_x_sample_sheet_validator._get_cycle(
        cycle_name=SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_2, nullable=nullable
    )

    # THEN the correct value is returned
    assert result == expected


def test_get_cycle_missing_cycle(novaseq_x_sample_sheet_validator: SampleSheetValidator, caplog):
    """Test that fetching a missing cycle value when nullable is False fails."""
    # GIVEN a sample sheet validator with a modified sample sheet content
    novaseq_x_sample_sheet_validator.content = [["not_a_cycle", 10]]
    assert len(novaseq_x_sample_sheet_validator.content) == 1

    # WHEN fetching the cycle value
    with pytest.raises(SampleSheetError):
        # THEN a SampleSheetError is raised
        novaseq_x_sample_sheet_validator._get_cycle(
            cycle_name=SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_2, nullable=False
        )
    assert (
        f"No {SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_2} found in sample sheet"
        in caplog.text
    )


def test_set_cycles(novaseq_x_sample_sheet_validator: SampleSheetValidator, caplog):
    """Test that the correct values for the cycles are set."""
    # GIVEN a sample sheet validator with a valid content and unset cycle values
    assert novaseq_x_sample_sheet_validator.read1_cycles is None
    assert novaseq_x_sample_sheet_validator.read2_cycles is None
    assert novaseq_x_sample_sheet_validator.index1_cycles is None
    assert novaseq_x_sample_sheet_validator.index2_cycles is None

    # WHEN setting the cycles
    novaseq_x_sample_sheet_validator.set_cycles()

    # THEN the correct values are set
    assert novaseq_x_sample_sheet_validator.read1_cycles == 151
    assert novaseq_x_sample_sheet_validator.read2_cycles == 151
    assert novaseq_x_sample_sheet_validator.index1_cycles == 10
    assert novaseq_x_sample_sheet_validator.index2_cycles == 10


@pytest.mark.parametrize(
    "sample_sheet_validator",
    [
        "hiseq_x_single_index_sample_sheet_validator",
        "hiseq_x_single_index_bcl2fastq_sample_sheet_validator",
        "hiseq_x_dual_index_sample_sheet_validator",
        "hiseq_x_dual_index_bcl2fastq_sample_sheet_validator",
        "hiseq_2500_dual_index_sample_sheet_validator",
        "hiseq_2500_dual_index_bcl2fastq_sample_sheet_validator",
        "hiseq_2500_custom_index_sample_sheet_validator",
        "hiseq_2500_custom_index_bcl2fastq_sample_sheet_validator",
        "novaseq_6000_pre_1_5_kits_sample_sheet_validator",
        "novaseq_6000_post_1_5_kits_sample_sheet_validator",
        "novaseq_x_sample_sheet_validator",
    ],
)
def test_validate_sample_sheet(sample_sheet_validator: str, request: FixtureRequest):
    """Test that a correct sample sheet passes validation."""
    # GIVEN a correct sample sheet and a sample sheet validator
    validator: SampleSheetValidator = request.getfixturevalue(sample_sheet_validator)

    # WHEN validating the sample sheet
    validator.validate_sample_sheet()

    # THEN no error is raised
