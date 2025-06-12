import pytest
from _pytest.fixtures import FixtureRequest

from cg.apps.demultiplex.sample_sheet.sample_sheet_validator import SampleSheetValidator
from cg.constants.demultiplexing import SampleSheetBCLConvertSections
from cg.exc import SampleSheetContentError, SampleSheetFormatError


@pytest.mark.parametrize(
    "sample_sheet_content",
    [
        "hiseq_x_single_index_sample_sheet_content",
        "hiseq_x_dual_index_sample_sheet_content",
        "hiseq_2500_dual_index_sample_sheet_content",
        "hiseq_2500_custom_index_sample_sheet_content",
        "novaseq_6000_pre_1_5_kits_sample_sheet_content",
        "novaseq_6000_post_1_5_kits_sample_sheet_content",
        "novaseq_x_sample_sheet_content",
    ],
    ids=[
        "HiSeqXSingleIndex",
        "HiSeqXDualIndex",
        "HiSeq2500DualIndex",
        "HiSeq2500CustomIndex",
        "NovaSeq6000Pre1.5Kits",
        "NovaSeq6000Post1.5Kits",
        "NovaSeqX",
    ],
)
def test_validate_all_sections_present(
    sample_sheet_validator: SampleSheetValidator,
    sample_sheet_content: str,
    request: FixtureRequest,
):
    """Test that when all sections are present in the sample sheet the validation passes."""
    # GIVEN a sample sheet content with all the required sections and a sample sheet validator
    content: list[list[str]] = request.getfixturevalue(sample_sheet_content)
    sample_sheet_validator.set_sample_sheet_content(content)

    # WHEN validating the sections of the sample sheet
    sample_sheet_validator._validate_all_sections_present()

    # THEN no error is raised


def test_validate_all_sections_present_missing_section(
    sample_sheet_validator: SampleSheetValidator,
    sample_sheet_content_missing_data_header: list[list[str]],
    caplog: pytest.LogCaptureFixture,
):
    """Test that when one sections is missing in the sample sheet the validation fails."""
    # GIVEN a sample sheet content with a missing section and a sample sheet validator
    sample_sheet_validator.set_sample_sheet_content(sample_sheet_content_missing_data_header)
    assert len(sample_sheet_validator.content) == 3

    # WHEN validating the sections of the sample sheet
    with pytest.raises(SampleSheetFormatError):
        # THEN a SampleSheetError is raised
        sample_sheet_validator._validate_all_sections_present()
    assert "Sample sheet does not have all the necessary sections" in caplog.text


@pytest.mark.parametrize(
    "sample_sheet_content, expected_index_settings_name",
    [
        ("novaseq_6000_pre_1_5_kits_sample_sheet_content", "NoReverseComplements"),
        ("novaseq_6000_post_1_5_kits_sample_sheet_content", "NovaSeq6000Post1.5Kits"),
        ("novaseq_x_sample_sheet_content", "NovaSeqX"),
    ],
    ids=["NovaSeq6000Pre1.5Kits", "NovaSeq6000Post1.5Kits", "NovaSeqX"],
)
def test_get_index_settings_name(
    sample_sheet_validator: SampleSheetValidator,
    sample_sheet_content: str,
    expected_index_settings_name: str,
    request: FixtureRequest,
):
    """Test that the correct index settings name is returned."""
    # GIVEN a sample sheet validator with a valid content
    sample_sheet_validator.set_sample_sheet_content(request.getfixturevalue(sample_sheet_content))

    # WHEN getting the index settings name
    index_settings_name: str = sample_sheet_validator._get_index_settings_name()

    # THEN the correct index settings name is returned
    assert index_settings_name == expected_index_settings_name


def test_get_index_settings_name_missing_index_settings(
    sample_sheet_validator: SampleSheetValidator,
    novaseq_x_sample_sheet_content: list[list[str]],
    caplog,
):
    """Test that getting the index settings from a sample sheet without it fails."""
    # GIVEN the content of a sample sheet without index settings
    novaseq_x_sample_sheet_content.pop(5)
    sample_sheet_validator.set_sample_sheet_content(novaseq_x_sample_sheet_content)
    assert [
        SampleSheetBCLConvertSections.Header.INDEX_SETTINGS.value,
        "NovaSeqX",
    ] not in sample_sheet_validator.content

    # WHEN getting the index settings name
    with pytest.raises(SampleSheetFormatError):
        # THEN a SampleSheetError is raised
        sample_sheet_validator._get_index_settings_name()
    assert "No index settings found in sample sheet" in caplog.text


@pytest.mark.parametrize(
    "sample_sheet_content, expected_reverse_complement",
    [
        ("novaseq_6000_pre_1_5_kits_sample_sheet_content", False),
        ("novaseq_6000_post_1_5_kits_sample_sheet_content", False),
        ("novaseq_x_sample_sheet_content", True),
    ],
    ids=["NovaSeq6000Pre1.5Kits", "NovaSeq6000Post1.5Kits", "NovaSeqX"],
)
def test_set_is_index2_reverse_complement(
    sample_sheet_validator: SampleSheetValidator,
    sample_sheet_content: str,
    expected_reverse_complement: bool,
    request: FixtureRequest,
):
    """Test that the correct value for index2 reverse complement value is set."""
    # GIVEN a sample sheet validator with a valid content
    sample_sheet_validator.set_sample_sheet_content(request.getfixturevalue(sample_sheet_content))

    # WHEN setting the index2 reverse complement value
    sample_sheet_validator._set_is_index2_reverse_complement()

    # THEN the correct value is set
    assert sample_sheet_validator.is_index2_reverse_complement == expected_reverse_complement


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
    sample_sheet_validator: SampleSheetValidator,
    sample_sheet_content: list[list[str]],
    nullable: bool,
    expected: int,
):
    """Test that a cycle value is fetched when the content is correct."""
    # GIVEN a sample sheet validator with a modified sample sheet content
    sample_sheet_validator.set_sample_sheet_content(sample_sheet_content)

    # WHEN fetching the cycle value
    result = sample_sheet_validator._get_cycle(
        cycle_name=SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_2, nullable=nullable
    )

    # THEN the correct value is returned
    assert result == expected


def test_get_cycle_missing_cycle(sample_sheet_validator: SampleSheetValidator, caplog):
    """Test that fetching a missing cycle value when nullable is False fails."""
    # GIVEN a sample sheet validator with a modified sample sheet content
    sample_sheet_validator.set_sample_sheet_content([["not_a_cycle", 10]])

    # WHEN fetching the cycle value
    with pytest.raises(SampleSheetFormatError):
        # THEN a SampleSheetError is raised
        sample_sheet_validator._get_cycle(
            cycle_name=SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_2, nullable=False
        )
    assert (
        f"No {SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_2} found in sample sheet"
        in caplog.text
    )


@pytest.mark.parametrize(
    "sample_sheet_content, expected_cycles",
    [
        ("hiseq_x_single_index_sample_sheet_content", [151, 151, 8, None]),
        ("hiseq_x_dual_index_sample_sheet_content", [151, 151, 8, 8]),
        ("hiseq_2500_dual_index_sample_sheet_content", [101, 101, 8, 8]),
        ("hiseq_2500_custom_index_sample_sheet_content", [101, 101, 17, 8]),
        ("novaseq_6000_pre_1_5_kits_sample_sheet_content", [151, 151, 10, 10]),
        ("novaseq_6000_post_1_5_kits_sample_sheet_content", [151, 151, 10, 10]),
        ("novaseq_x_sample_sheet_content", [151, 151, 10, 10]),
    ],
    ids=[
        "HiSeqXSingleIndex",
        "HiSeqXDualIndex",
        "HiSeq2500DualIndex",
        "HiSeq2500CustomIndex",
        "NovaSeq6000Pre1.5Kits",
        "NovaSeq6000Post1.5Kits",
        "NovaSeqX",
    ],
)
def test_set_cycles(
    sample_sheet_validator: SampleSheetValidator,
    sample_sheet_content: str,
    expected_cycles: list[int | None],
    request: FixtureRequest,
    caplog,
):
    """Test that the correct values for the cycles are set."""
    # GIVEN a valid sample sheet content
    content: list[list[str]] = request.getfixturevalue(sample_sheet_content)
    sample_sheet_validator.set_sample_sheet_content(content)

    # GIVEN a sample sheet validator with no cycles set
    assert sample_sheet_validator.read1_cycles is None
    assert sample_sheet_validator.read2_cycles is None
    assert sample_sheet_validator.index1_cycles is None
    assert sample_sheet_validator.index2_cycles is None

    # WHEN setting the cycles
    sample_sheet_validator._set_cycles()

    # THEN the correct values set as expected
    assert sample_sheet_validator.read1_cycles == expected_cycles[0]
    assert sample_sheet_validator.read2_cycles == expected_cycles[1]
    assert sample_sheet_validator.index1_cycles == expected_cycles[2]
    assert sample_sheet_validator.index2_cycles == expected_cycles[3]


@pytest.mark.parametrize(
    "sample_sheet_content",
    [
        "novaseq_6000_sample_sheet_with_reversed_cycles_content",
        "novaseq_x_sample_sheet_with_forward_cycles_content",
    ],
)
def test_validate_override_cycles_incorrect_cycles(
    sample_sheet_validator: SampleSheetValidator, sample_sheet_content: str, request: FixtureRequest
):
    """Test that a sample sheets with incorrect override cycles raise an error."""
    # GIVEN a sample sheet with incorrect override cycles
    sample_sheet_validator.set_sample_sheet_content(request.getfixturevalue(sample_sheet_content))

    # WHEN validating the override cycles
    with pytest.raises(SampleSheetContentError):
        # THEN a SampleSheetError is raised
        sample_sheet_validator._validate_override_cycles()


@pytest.mark.parametrize(
    "sample_sheet_content",
    [
        "hiseq_x_single_index_sample_sheet_content",
        "hiseq_x_dual_index_sample_sheet_content",
        "hiseq_2500_dual_index_sample_sheet_content",
        "hiseq_2500_custom_index_sample_sheet_content",
        "novaseq_6000_pre_1_5_kits_sample_sheet_content",
        "novaseq_6000_post_1_5_kits_sample_sheet_content",
        "novaseq_x_sample_sheet_content",
    ],
    ids=[
        "HiSeqXSingleIndex",
        "HiSeqXDualIndex",
        "HiSeq2500DualIndex",
        "HiSeq2500CustomIndex",
        "NovaSeq6000Pre1.5Kits",
        "NovaSeq6000Post1.5Kits",
        "NovaSeqX",
    ],
)
def test_validate_sample_sheet_from_content(
    sample_sheet_validator: SampleSheetValidator,
    sample_sheet_content: str,
    request: FixtureRequest,
):
    """Test that a correct sample sheet passes validation."""
    # GIVEN sample sheet validator and a correct sample sheet content
    content: list[list[str]] = request.getfixturevalue(sample_sheet_content)

    # WHEN validating the sample sheet
    sample_sheet_validator.validate_sample_sheet_from_content(content)

    # THEN no error is raised
