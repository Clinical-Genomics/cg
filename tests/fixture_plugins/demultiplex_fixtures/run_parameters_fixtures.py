from pathlib import Path

import pytest

from cg.services.run_parameters_service.run_parameters_service import (
    RunParametersServiceHiSeq,
    RunParametersServiceNovaSeq6000,
    RunParametersServiceNovaSeqX,
)


@pytest.fixture(scope="function")
def run_parameters_hiseq_different_index(run_parameters_dir: Path) -> RunParametersServiceHiSeq:
    """Return a HiSeq RunParameters object with different index cycles."""
    path = Path(run_parameters_dir, "RunParameters_hiseq_2500_different_index_cycles.xml")
    return RunParametersServiceHiSeq(run_parameters_path=path)


@pytest.fixture(scope="function")
def run_parameters_novaseq_6000_different_index(
    run_parameters_dir: Path,
) -> RunParametersServiceNovaSeq6000:
    """Return a NovaSeq6000 RunParameters object with different index cycles."""
    path = Path(run_parameters_dir, "RunParameters_novaseq_6000_different_index_cycles.xml")
    return RunParametersServiceNovaSeq6000(run_parameters_path=path)


@pytest.fixture(scope="function")
def run_parameters_novaseq_x_different_index(
    run_parameters_dir: Path,
) -> RunParametersServiceNovaSeqX:
    """Return a NovaSeqX RunParameters object with different index cycles."""
    path = Path(run_parameters_dir, "RunParameters_novaseq_X_different_index_cycles.xml")
    return RunParametersServiceNovaSeqX(run_parameters_path=path)


@pytest.fixture(scope="session")
def hiseq_x_single_index_run_parameters(
    hiseq_x_single_index_run_parameters_path: Path,
) -> RunParametersServiceHiSeq:
    """Return a HiSeqX run parameters object with single index."""
    return RunParametersServiceHiSeq(run_parameters_path=hiseq_x_single_index_run_parameters_path)


@pytest.fixture(scope="session")
def hiseq_x_dual_index_run_parameters(
    hiseq_x_dual_index_run_parameters_path: Path,
) -> RunParametersServiceHiSeq:
    """Return a HiSeqX run parameters object with dual index."""
    return RunParametersServiceHiSeq(run_parameters_path=hiseq_x_dual_index_run_parameters_path)


@pytest.fixture(scope="session")
def hiseq_2500_dual_index_run_parameters(
    hiseq_2500_dual_index_run_parameters_path: Path,
) -> RunParametersServiceHiSeq:
    """Return a HiSeq2500 run parameters object with dual index."""
    return RunParametersServiceHiSeq(run_parameters_path=hiseq_2500_dual_index_run_parameters_path)


@pytest.fixture(scope="session")
def hiseq_2500_custom_index_run_parameters(
    hiseq_2500_custom_index_run_parameters_path: Path,
) -> RunParametersServiceHiSeq:
    """Return a HiSeq2500 run parameters object with custom index."""
    return RunParametersServiceHiSeq(
        run_parameters_path=hiseq_2500_custom_index_run_parameters_path
    )


@pytest.fixture
def novaseq_6000_run_parameters_pre_1_5_kits(
    novaseq_6000_run_parameters_pre_1_5_kits_path: Path,
) -> RunParametersServiceNovaSeq6000:
    """Return a NovaSeq6000 run parameters pre 1.5 kit object."""
    return RunParametersServiceNovaSeq6000(
        run_parameters_path=novaseq_6000_run_parameters_pre_1_5_kits_path
    )


@pytest.fixture
def novaseq_6000_run_parameters_post_1_5_kits(novaseq_6000_run_parameters_post_1_5_kits_path: Path):
    """Return a NovaSeq6000 run parameters post 1.5 kit object."""
    return RunParametersServiceNovaSeq6000(
        run_parameters_path=novaseq_6000_run_parameters_post_1_5_kits_path
    )


@pytest.fixture
def novaseq_x_run_parameters(
    novaseq_x_run_parameters_path: Path,
) -> RunParametersServiceNovaSeqX:
    """Return a NovaSeqX run parameters object."""
    return RunParametersServiceNovaSeqX(run_parameters_path=novaseq_x_run_parameters_path)
