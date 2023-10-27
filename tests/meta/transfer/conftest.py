from pathlib import Path
from typing import Generator

import pytest

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.meta.transfer import TransferLims
from cg.store import Store
from tests.mocks.limsmock import MockLimsAPI


@pytest.fixture(name="transfer_lims_api")
def transfer_lims_api(sample_store: Store) -> Generator[TransferLims, None, None]:
    """Setup LIMS transfer API."""
    yield TransferLims(sample_store, MockLimsAPI(config=""))


@pytest.fixture(scope="session")
def external_data_directory(
    tmpdir_factory, customer_id: str, cust_sample_id: str, ticket_id: str
) -> Path:
    """Returns a customer folder with fastq.gz files in sample-directories."""
    cust_folder: Path = tmpdir_factory.mktemp(customer_id, numbered=False)
    ticket_folder: Path = Path(cust_folder, ticket_id)
    ticket_folder.mkdir()
    samples: list[str] = [f"{cust_sample_id}1", f"{cust_sample_id}2"]
    for sample in samples:
        Path(ticket_folder, sample).mkdir(exist_ok=True, parents=True)
        for read in [1, 2]:
            Path(ticket_folder, sample, f"{sample}_fastq_{read}.fastq.gz").touch(exist_ok=True)
            Path(ticket_folder, sample, f"{sample}_fastq_{read}.fastq.gz.md5").touch(exist_ok=True)
    return Path(ticket_folder)


@pytest.fixture(name="sample_sheet_path")
def sample_sheet_path(tmpdir_factory) -> Generator[Path, None, None]:
    """Create and return path to sample sheet."""
    sample_sheet_path_dir: Path = Path(tmpdir_factory.mktemp("DEMUX"), "HVKJCDRXX", "NAADM1")
    sample_sheet_path_dir.mkdir(parents=True, exist_ok=True)
    sample_sheet_path: Path = Path(
        sample_sheet_path_dir, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
    )
    sample_sheet_path.touch()
    yield sample_sheet_path
