from typing import List, Generator

import pytest

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.meta.transfer import TransferLims
from cg.store import Store
from pathlib import Path

from tests.mocks.limsmock import MockLimsAPI


@pytest.fixture(name="transfer_lims_api")
def fixture_transfer_lims_api(sample_store: Store) -> Generator[TransferLims, None, None]:
    """Setup LIMS transfer API."""
    yield TransferLims(sample_store, MockLimsAPI(config=""))


@pytest.fixture(name="external_data_directory", scope="session")
def external_data_directory(
    tmpdir_factory, tmp_path_factory, customer_id: str, cust_sample_id: str
) -> Path:
    """Returns a customer folder with fastq.gz files in sample-directories."""
    cust_folders: List[Path] = []
    for cust_number in range(2):
        cust_folders.append(tmpdir_factory.mktemp(f"cust00{cust_number}", numbered=False))
        for sample_number in range(2):
            sample_dir: Path = Path(
                tmpdir_factory.mktemp(
                    f"cust00{cust_number}/cust00{cust_number}_sample{sample_number}", numbered=False
                )
            )
            for fastq_number in range(2):
                sample_dir.joinpath(f"fastq_{fastq_number}").touch()
    return cust_folders[0].parent


@pytest.fixture(name="sample_sheet_path")
def fixture_sample_sheet_path(tmpdir_factory) -> Generator[Path, None, None]:
    """Create and return path to sample sheet."""
    sample_sheet_path_dir: Path = Path(tmpdir_factory.mktemp("DEMUX"), "HVKJCDRXX", "NAADM1")
    sample_sheet_path_dir.mkdir(parents=True, exist_ok=True)
    sample_sheet_path: Path = Path(
        sample_sheet_path_dir, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
    )
    sample_sheet_path.touch()
    yield sample_sheet_path


@pytest.fixture(name="cgstats_log_path")
def fixture_cgstats_log_path(tmpdir_factory) -> Generator[Path, None, None]:
    """Create and return path to cgstats log file."""
    cgstats_log_path_dir: Path = Path(tmpdir_factory.mktemp("DEMUX"), "HVKJCDRXX", "NAADM1")
    cgstats_log_path_dir.mkdir(parents=True, exist_ok=True)
    cgstats_log_path: Path = Path(cgstats_log_path_dir, "stats-121087-flow-cell-id.txt")
    cgstats_log_path.touch()
    yield cgstats_log_path
