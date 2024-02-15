import pytest
from _pytest.fixtures import FixtureRequest

from cg.apps.demultiplex.sample_sheet.sample_sheet_validator import (
    FORWARD_INDEX_CYCLE_PATTERN,
    REVERSE_INDEX_CYCLE_PATTERN,
    OverrideCyclesValidator,
)


@pytest.mark.skip(reason="Test is not implemented")
@pytest.mark.parametrize(
    "pattern, index_cycle, run_cycles, expected",
    [(FORWARD_INDEX_CYCLE_PATTERN, "I8N2", 10, True)],
)
def test_is_index_cycle_value_following_pattern(
    pattern: str,
    index_cycle: str,
    run_cycles: int,
    expected: bool,
    index1_sequence_from_lims: str,
    request: FixtureRequest,
):
    """Test that index cycles are recognised following a pattern."""
    # GIVEN an override cycles validator, a pattern and a sample
    reverse_complement: bool = pattern == REVERSE_INDEX_CYCLE_PATTERN
    validator = OverrideCyclesValidator(
        run_read1_cycles=151,
        run_read2_cycles=151,
        run_index1_cycles=run_cycles,
        run_index2_cycles=None,
        is_reverse_complement=reverse_complement,
    )

    # WHEN checking if the index cycle value is following the pattern
    result: bool = validator.is_index_cycle_value_following_pattern(
        pattern=pattern,
        index_cycle=index_cycle,
        run_cycles=validator.run_index1_cycles,
        index_sequence=index1_sequence_from_lims,
    )

    # THEN assert that the index cycles are following the pattern
    assert result == expected
