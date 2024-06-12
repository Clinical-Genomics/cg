from pathlib import Path

import pytest

from cg.models.demultiplex.run_parameters import (
    RunParametersHiSeq,
    RunParametersNovaSeq6000,
    RunParametersNovaSeqX,
)


@pytest.fixture(scope="function")
def run_parameters_hiseq_different_index(run_parameters_dir: Path) -> RunParametersHiSeq:
    """Return a HiSeq RunParameters object with different index cycles."""
    path = Path(run_parameters_dir, "RunParameters_hiseq_2500_different_index_cycles.xml")
    return RunParametersHiSeq(run_parameters_path=path)


@pytest.fixture(scope="function")
def run_parameters_novaseq_6000_different_index(
    run_parameters_dir: Path,
) -> RunParametersNovaSeq6000:
    """Return a NovaSeq6000 RunParameters object with different index cycles."""
    path = Path(run_parameters_dir, "RunParameters_novaseq_6000_different_index_cycles.xml")
    return RunParametersNovaSeq6000(run_parameters_path=path)


@pytest.fixture(scope="function")
def run_parameters_novaseq_x_different_index(
    run_parameters_dir: Path,
) -> RunParametersNovaSeqX:
    """Return a NovaSeqX RunParameters object with different index cycles."""
    path = Path(run_parameters_dir, "RunParameters_novaseq_X_different_index_cycles.xml")
    return RunParametersNovaSeqX(run_parameters_path=path)


@pytest.fixture(scope="session")
def hiseq_x_single_index_run_parameters(
    hiseq_x_single_index_run_parameters_path: Path,
) -> RunParametersHiSeq:
    """Return a HiSeqX run parameters object with single index."""
    return RunParametersHiSeq(run_parameters_path=hiseq_x_single_index_run_parameters_path)


@pytest.fixture(scope="session")
def hiseq_x_dual_index_run_parameters(
    hiseq_x_dual_index_run_parameters_path: Path,
) -> RunParametersHiSeq:
    """Return a HiSeqX run parameters object with dual index."""
    return RunParametersHiSeq(run_parameters_path=hiseq_x_dual_index_run_parameters_path)


@pytest.fixture(scope="session")
def hiseq_2500_dual_index_run_parameters(
    hiseq_2500_dual_index_run_parameters_path: Path,
) -> RunParametersHiSeq:
    """Return a HiSeq2500 run parameters object with dual index."""
    return RunParametersHiSeq(run_parameters_path=hiseq_2500_dual_index_run_parameters_path)


@pytest.fixture(scope="session")
def hiseq_2500_custom_index_run_parameters(
    hiseq_2500_custom_index_run_parameters_path: Path,
) -> RunParametersHiSeq:
    """Return a HiSeq2500 run parameters object with custom index."""
    return RunParametersHiSeq(run_parameters_path=hiseq_2500_custom_index_run_parameters_path)


@pytest.fixture
def novaseq_6000_run_parameters_pre_1_5_kits(
    novaseq_6000_run_parameters_pre_1_5_kits_path: Path,
) -> RunParametersNovaSeq6000:
    """Return a NovaSeq6000 run parameters pre 1.5 kit object."""
    return RunParametersNovaSeq6000(
        run_parameters_path=novaseq_6000_run_parameters_pre_1_5_kits_path
    )


@pytest.fixture
def novaseq_6000_run_parameters_post_1_5_kits(novaseq_6000_run_parameters_post_1_5_kits_path: Path):
    """Return a NovaSeq6000 run parameters post 1.5 kit object."""
    return RunParametersNovaSeq6000(
        run_parameters_path=novaseq_6000_run_parameters_post_1_5_kits_path
    )


@pytest.fixture
def novaseq_x_run_parameters(
    novaseq_x_run_parameters_path: Path,
) -> RunParametersNovaSeqX:
    """Return a NovaSeqX run parameters object."""
    return RunParametersNovaSeqX(run_parameters_path=novaseq_x_run_parameters_path)
