from typing import List, Generator

import pytest
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
