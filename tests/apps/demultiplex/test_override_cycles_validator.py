import pytest

from cg.apps.demultiplex.sample_sheet.override_cycles_validator import OverrideCyclesValidator
from cg.constants.demultiplexing import FORWARD_INDEX_CYCLE_PATTERN, REVERSE_INDEX_CYCLE_PATTERN
from cg.exc import OverrideCyclesError


@pytest.mark.parametrize(
    "pattern, index_cycle, run_cycles, expected",
    [
        (FORWARD_INDEX_CYCLE_PATTERN, "I8N2", 10, True),
        (REVERSE_INDEX_CYCLE_PATTERN, "I8N2", 10, False),
        (FORWARD_INDEX_CYCLE_PATTERN, "N2I8", 10, False),
        (REVERSE_INDEX_CYCLE_PATTERN, "N2I8", 10, True),
        (FORWARD_INDEX_CYCLE_PATTERN, "NOT_A_CYCLE6N8", 10, False),
        (r"(\d+)", "I8N2", 10, False),
    ],
    ids=[
        "forward_valid",
        "reverse_invalid",
        "forward_invalid",
        "reverse_valid",
        "not_a_cycle",
        "not_a_pattern",
    ],
)
def test_is_index_cycle_value_following_pattern(
    override_cycles_validator: OverrideCyclesValidator,
    index2_8_nt_sequence_from_lims: str,
    pattern: str,
    index_cycle: str,
    run_cycles: int,
    expected: bool,
):
    """Test if an index follows a pattern works correctly."""
    # GIVEN an override cycles validator, an index sequence

    # WHEN checking if the index cycle value follows a pattern
    result: bool = override_cycles_validator._is_index_cycle_value_following_pattern(
        pattern=pattern,
        index_cycle=index_cycle,
        run_cycles=run_cycles,
        index_sequence=index2_8_nt_sequence_from_lims,
    )

    # THEN the result should be as expected
    assert result == expected


def test_validate_reads_cycles_correct_cycles(
    override_cycles_validator: OverrideCyclesValidator,
    forward_index2_cycle_processed_flow_cell_8_nt_sample: dict[str, str],
):
    """Test that a sample with correct read cycle values passes validation."""
    # GIVEN an override cycles validator with read cycles set
    override_cycles_validator.set_run_cycles(read1_cycles=151, read2_cycles=151)

    # GIVEN a sample with correct read cycle values
    override_cycles_validator.set_attributes_from_sample(
        forward_index2_cycle_processed_flow_cell_8_nt_sample
    )

    # WHEN validating the read cycles
    override_cycles_validator._validate_reads_cycles()

    # THEN no exception is raised


@pytest.mark.parametrize(
    "wrong_override_cycles",
    [
        "Y101;I8N2;I8N2;Y101",
        "Y151,I8N2,N2I8,Y151",
        "Y151;I8N2;",
        "NotAValidCycle",
    ],
    ids=["wrong_values", "wrong_separator", "missing_cycle", "not_a_valid_cycle"],
)
def test_validate_reads_cycles_incorrect_cycles(
    override_cycles_validator: OverrideCyclesValidator,
    processed_flow_cell_sample_8_index: dict[str, str],
    wrong_override_cycles: str,
    caplog: pytest.LogCaptureFixture,
):
    """Test that a sample with incorrect read cycle values raises an exception."""
    # GIVEN an override cycles validator read cycles set
    override_cycles_validator.set_run_cycles(read1_cycles=151, read2_cycles=151)

    # GIVEN a sample with incorrect read cycle values
    processed_flow_cell_sample_8_index["OverrideCycles"] = wrong_override_cycles
    override_cycles_validator.set_attributes_from_sample(processed_flow_cell_sample_8_index)

    # WHEN validating the read cycles
    with pytest.raises(OverrideCyclesError):
        override_cycles_validator._validate_reads_cycles()
    assert "Incorrect read cycles" in caplog.text


@pytest.mark.parametrize(
    "sample",
    [
        "forward_index2_cycle_processed_flow_cell_8_nt_sample",
        "reverse_index2_cycle_processed_flow_cell_8_nt_sample",
    ],
)
def test_validate_index1_cycles_correct_cycles(
    override_cycles_validator: OverrideCyclesValidator, sample: str, request: pytest.FixtureRequest
):
    """Test that a sample with correct index 1 cycle values passes validation."""
    # GIVEN an override cycles validator with index 1 cycles set
    override_cycles_validator.set_run_cycles(index1_cycles=10)

    # GIVEN a sample with correct index 1 cycle values
    override_cycles_validator.set_attributes_from_sample(request.getfixturevalue(sample))

    # WHEN validating the index 1 cycles
    override_cycles_validator._validate_index1_cycles()

    # THEN no exception is raised


@pytest.mark.parametrize(
    "run_index1_cycles,wrong_override_cycles",
    [
        (10, "Y151;N2I8;I8N2;Y151"),
        (10, "Y151;I10;I8N2;Y151"),
        (10, "Y151;I8;I8;Y151"),
        (10, "Y151;I8N9;I8;Y151"),
        (8, "Y151;I8N2;I8N2;Y151"),
        (8, "Y151;I10;N2I8;Y151"),
    ],
    ids=[
        "reverse_index1",
        "too_many_cycles",
        "missing_ignored_cycles",
        "custom_index_length",
        "extra_ignored_cycles",
        "extra_cycles",
    ],
)
def test_validate_index1_cycles_incorrect_cycles(
    override_cycles_validator: OverrideCyclesValidator,
    processed_flow_cell_sample_8_index: dict[str, str],
    run_index1_cycles: int,
    wrong_override_cycles: str,
    caplog: pytest.LogCaptureFixture,
):
    """Test that a sample with incorrect index 1 cycle values raises an exception."""
    # GIVEN an override cycles validator with index 1 cycles set
    override_cycles_validator.set_run_cycles(index1_cycles=run_index1_cycles)

    # GIVEN a sample with incorrect index 1 cycle values
    processed_flow_cell_sample_8_index["OverrideCycles"] = wrong_override_cycles
    override_cycles_validator.set_attributes_from_sample(processed_flow_cell_sample_8_index)

    # WHEN validating the index 1 cycles
    with pytest.raises(OverrideCyclesError):
        override_cycles_validator._validate_index1_cycles()
    assert "Incorrect index1 cycle" in caplog.text


@pytest.mark.parametrize(
    "sample, reverse_complement",
    [
        ("forward_index2_cycle_processed_flow_cell_8_nt_sample", False),
        ("reverse_index2_cycle_processed_flow_cell_8_nt_sample", True),
    ],
)
def test_validate_index2_cycles_correct_cycles(
    override_cycles_validator: OverrideCyclesValidator,
    sample: str,
    reverse_complement: bool,
    request: pytest.FixtureRequest,
):
    """Test that a sample with correct index 2 cycle values passes validation."""
    # GIVEN an override cycles validator with index 2 cycles and reverse complement set
    override_cycles_validator.set_run_cycles(index2_cycles=10)
    override_cycles_validator.set_reverse_complement(reverse_complement)

    # GIVEN a sample with correct index 2 cycle values
    override_cycles_validator.set_attributes_from_sample(request.getfixturevalue(sample))

    # WHEN validating the index 2 cycles
    override_cycles_validator._validate_index2_cycles()

    # THEN no exception is raised


@pytest.mark.parametrize(
    "run_index2_cycles,wrong_override_cycles,reverse_complement",
    [
        (10, "Y151;I8N2;I8N2;Y151", True),
        (10, "Y151;I8N2;N2I8;Y151", False),
        (10, "Y151;I8N2;I10;Y151", True),
        (10, "Y151;I8N2;I8;Y151", True),
        (10, "Y151;I8N2;I8N9;Y151", True),
        (8, "Y151;I8N2;I8N2;Y151", True),
        (8, "Y151;I8N2;I10;Y151", True),
    ],
    ids=[
        "forward_index2",
        "reverse_index2",
        "too_many_cycles",
        "missing_ignored_cycles",
        "custom_index_length",
        "extra_ignored_cycles",
        "extra_cycles",
    ],
)
def test_validate_index2_cycles_incorrect_cycles(
    override_cycles_validator: OverrideCyclesValidator,
    processed_flow_cell_sample_8_index: dict[str, str],
    run_index2_cycles: int,
    wrong_override_cycles: str,
    reverse_complement: bool,
    caplog: pytest.LogCaptureFixture,
):
    """Test that a sample with incorrect index 2 cycle values raises an exception."""
    # GIVEN an override cycles validator with index 2 cycles and reverse complement set
    override_cycles_validator.set_run_cycles(index2_cycles=run_index2_cycles)
    override_cycles_validator.set_reverse_complement(reverse_complement)

    # GIVEN a sample with incorrect index 2 cycle values
    processed_flow_cell_sample_8_index["OverrideCycles"] = wrong_override_cycles
    override_cycles_validator.set_attributes_from_sample(processed_flow_cell_sample_8_index)

    # WHEN validating the index 2 cycles
    with pytest.raises(OverrideCyclesError):
        override_cycles_validator._validate_index2_cycles()
    assert "does not match with run cycle" in caplog.text


@pytest.mark.parametrize(
    "sample, reverse_complement",
    [
        ("forward_index2_cycle_processed_flow_cell_8_nt_sample", False),
        ("reverse_index2_cycle_processed_flow_cell_8_nt_sample", True),
        ("processed_flow_cell_10_nt_sample", False),
    ],
    ids=["forward_8_nt", "reverse_8_nt", "10_nt"],
)
def test_validate_sample(
    override_cycles_validator: OverrideCyclesValidator,
    sample: str,
    reverse_complement: bool,
    request: pytest.FixtureRequest,
):
    """Test that a sample with correct override cycles passes validation."""
    # GIVEN a sample with correct override cycles

    # GIVEN an override cycles validator with all parameters set
    override_cycles_validator.set_run_cycles(
        read1_cycles=151, read2_cycles=151, index1_cycles=10, index2_cycles=10
    )
    override_cycles_validator.set_reverse_complement(reverse_complement)
    override_cycles_validator.set_attributes_from_sample(request.getfixturevalue(sample))

    # WHEN validating the sample
    override_cycles_validator.validate_sample(request.getfixturevalue(sample))

    # THEN no exception is raised
