import datetime as dt
from os import utime
from typing import List, Generator
import pytest

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.meta.external_data import ExternalDataHandler
from cg.meta.transfer import TransferLims
from cg.models.cg_config import CGConfig
from cg.store import Store
from pathlib import Path

from tests.mocks.limsmock import MockLimsAPI


@pytest.fixture(name="transfer_lims_api")
def fixture_transfer_lims_api(sample_store: Store) -> Generator[TransferLims, None, None]:
    """Setup LIMS transfer API."""
    yield TransferLims(sample_store, MockLimsAPI(config=""))


@pytest.fixture(name="external_data_handler")
def fixture_external_data_handler(
    external_data_context: CGConfig, external_data_directory: Path
) -> ExternalDataHandler:
    """ExternalDataHandler fixture."""
    external_data_handler: ExternalDataHandler = ExternalDataHandler(config=external_data_context)
    external_data_handler.external_data_dir = external_data_directory
    return external_data_handler


@pytest.fixture(name="external_data_context")
def fixture_external_data_context(cg_context: CGConfig, helpers, external_data_directory: Path):
    """Sets up a external_data file structure and adds cases to status_db."""
    for customer_dir in external_data_directory.iterdir():
        helpers.ensure_customer(store=cg_context.status_db, customer_id=customer_dir.name)
        for sample_dir in customer_dir.iterdir():
            helpers.add_sample(
                store=cg_context.status_db, name=sample_dir.name, customer_id=customer_dir.name
            )
    cg_context.status_db.close()
    return cg_context


@pytest.fixture(name="external_data_directory", scope="session")
def fixture_external_data_directory(
    tmpdir_factory, tmp_path_factory, customer_id: str, cust_sample_id: str
) -> Path:
    """Returns a mimic external data folder customer folders containing sample-directories with
    empty files."""
    external_data_directory: Path = Path(tmpdir_factory.mktemp("external_data", numbered=False))
    for cust_number in range(2):
        customer_folder: Path = Path(external_data_directory, f"cust00{cust_number}")
        Path.mkdir(customer_folder)
        for sample_number in range(2):
            sample_dir: Path = Path(
                f"{customer_folder}", f"cust00{cust_number}_sample{sample_number}"
            )
            Path.mkdir(sample_dir)
            for fastq_number in range(2):
                sample_dir.joinpath(
                    f"cust00{cust_number}_sample{sample_number}_fastq_{fastq_number}"
                ).touch()
            utime(
                path=sample_dir,
                ns=(
                    (dt.datetime.now() - dt.timedelta(hours=5)).microsecond * 1000,
                    (dt.datetime.now() - dt.timedelta(hours=5)).microsecond * 1000,
                ),
            )

    return external_data_directory


@pytest.fixture(name="external_data_sample_folder", scope="session")
def fixture_external_data_sample_folder(external_data_directory: Path) -> Path:
    """Returns a customer folder with fastq.gz files in sample-directories."""
    customer_folder: Path = next(external_data_directory.iterdir())
    return next(customer_folder.iterdir())


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
