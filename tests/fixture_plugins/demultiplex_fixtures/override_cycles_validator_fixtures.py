import pytest

from cg.apps.demultiplex.sample_sheet.sample_sheet_validator import OverrideCyclesValidator


@pytest.fixture
def hiseq_x_single_index_override_cycles_validator() -> OverrideCyclesValidator:
    """Return a HiseqX single index override cycles validator."""
    return OverrideCyclesValidator(
        run_read1_cycles=151,
        run_read2_cycles=151,
        run_index1_cycles=8,
        run_index2_cycles=None,
        is_reverse_complement=False,
    )


@pytest.fixture
def hiseq_x_dual_index_override_cycles_validator() -> OverrideCyclesValidator:
    """Return a HiseqX dual index override cycles validator."""
    return OverrideCyclesValidator(
        run_read1_cycles=151,
        run_read2_cycles=151,
        run_index1_cycles=8,
        run_index2_cycles=8,
        is_reverse_complement=False,
    )


@pytest.fixture
def hiseq_2500_dual_index_override_cycles_validator() -> OverrideCyclesValidator:
    """Return a Hiseq 2500 dual index override cycles validator."""
    return OverrideCyclesValidator(
        run_read1_cycles=101,
        run_read2_cycles=101,
        run_index1_cycles=8,
        run_index2_cycles=8,
        is_reverse_complement=False,
    )


@pytest.fixture
def hiseq_2500_custom_index_override_cycles_validator() -> OverrideCyclesValidator:
    """Return a Hiseq 2500 custom index override cycles validator."""
    return OverrideCyclesValidator(
        run_read1_cycles=101,
        run_read2_cycles=101,
        run_index1_cycles=17,
        run_index2_cycles=8,
        is_reverse_complement=False,
    )


@pytest.fixture
def novaseq_6000_pre_1_5_kits_override_cycles_validator() -> OverrideCyclesValidator:
    """Return a NovaSeq 6000 pre 1.5 kits override cycles validator."""
    return OverrideCyclesValidator(
        run_read1_cycles=151,
        run_read2_cycles=151,
        run_index1_cycles=10,
        run_index2_cycles=10,
        is_reverse_complement=False,
    )


@pytest.fixture
def novaseq_6000_post_1_5_kits_override_cycles_validator() -> OverrideCyclesValidator:
    """Return a NovaSeq 6000 post 1.5 kits override cycles validator."""
    return OverrideCyclesValidator(
        run_read1_cycles=151,
        run_read2_cycles=151,
        run_index1_cycles=10,
        run_index2_cycles=10,
        is_reverse_complement=False,
    )


@pytest.fixture
def novaseq_x_override_cycles_validator() -> OverrideCyclesValidator:
    """Return a NovaSeqX override cycles validator."""
    return OverrideCyclesValidator(
        run_read1_cycles=151,
        run_read2_cycles=151,
        run_index1_cycles=10,
        run_index2_cycles=10,
        is_reverse_complement=True,
    )
