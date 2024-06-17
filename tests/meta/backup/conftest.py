import fnmatch
from pathlib import Path
from typing import Callable

import pytest

from cg.constants import FileExtensions
from cg.meta.backup.backup import BackupAPI
from cg.meta.backup.pdc import PdcAPI
from cg.meta.encryption.encryption import EncryptionAPI
from cg.meta.tar.tar import TarAPI
from cg.models.cg_config import PDCArchivingDirectory
from cg.models.cg_config import CGConfig
from cg.store.store import Store


@pytest.fixture
def mock_pdc_query_method(archived_flow_cells: list[str]) -> Callable:
    """Returns a mock method mimicking the pattern search made by the dsmc q archive command."""

    def mock_method(search_pattern: str) -> list[str] | None:
        if match := fnmatch.filter(archived_flow_cells, search_pattern):
            return match

    return mock_method


@pytest.fixture
def dsmc_q_archive_output() -> list[str]:
    output: str = """IBM Tivoli Storage Manager
Command Line Backup-Archive Client Interface
  Client Version 7, Release 1, Level 4.0
  Client date/time: 09/22/2023 10:42:42
(c) Copyright by IBM Corporation and other(s) 1990, 2015. All Rights Reserved.

Node Name: HASTA.SCILIFELAB.SE_CLINICAL
Session established with server BLACKHOLE: Linux/x86_64
  Server Version 8, Release 1, Level 9.300
  Server date/time: 09/22/2023 10:42:42  Last access: 09/22/2023 10:42:26

Accessing as node: SLLCLINICAL
             Size  Archive Date - Time    File - Expires on - Description
             ----  -------------------    -------------------------------
           607  B  04/07/2019 07:30:15    /home/hiseq.clinical/ENCRYPT/190329_A00689_0018_AHVKJCDRXX.key.gpg Never Archive Date: 04/07/2019
 1,244,997,334 KB  04/07/2019 04:00:05    /home/hiseq.clinical/ENCRYPT/190329_A00689_0018_AHVKJCDRXX.tar.gz.gpg Never Archive Date: 04/07/2019"""
    return output.splitlines()


@pytest.fixture
def archived_flow_cells(pdc_archiving_directory: PDCArchivingDirectory) -> list[str]:
    """Returns a list of archived flow cells."""
    return [
        f"{pdc_archiving_directory.current}/new_flow_cell{FileExtensions.TAR}{FileExtensions.GZIP}{FileExtensions.GPG}",
        f"{pdc_archiving_directory.nas}/old_flow_cell{FileExtensions.TAR}{FileExtensions.GZIP}{FileExtensions.GPG}",
        f"{pdc_archiving_directory.pre_nas}/ancient_flow_cell{FileExtensions.TAR}{FileExtensions.GZIP}{FileExtensions.GPG}",
    ]


@pytest.fixture
def backup_api(cg_context: CGConfig, illumina_sequencing_runs_directory: Path) -> BackupAPI:
    """Return a BackupAPI instance."""
    encryption_api: EncryptionAPI = EncryptionAPI(
        binary_path=cg_context.encryption.binary_path, dry_run=True
    )
    store: Store = cg_context.status_db
    tar_api: TarAPI = TarAPI(binary_path=cg_context.tar.binary_path, dry_run=True)
    pdc_api: PdcAPI = PdcAPI(binary_path=cg_context.pdc.binary_path, dry_run=True)

    pdc_archiving_directory: PDCArchivingDirectory = cg_context.backup.pdc_archiving_directory
    _backup_api: BackupAPI = BackupAPI(
        encryption_api=encryption_api,
        status=store,
        tar_api=tar_api,
        pdc_api=pdc_api,
        pdc_archiving_directory=pdc_archiving_directory,
        flow_cells_dir=illumina_sequencing_runs_directory,
        dry_run=True,
    )
    return _backup_api


@pytest.fixture
def spring_file_path() -> Path:
    """Return spring file path"""
    return Path("/path/to/spring_file.spring")


@pytest.fixture
def backup_file_path() -> str:
    """Return path to a file used in the backup process"""
    return "/path/to/backup_file.extension"


@pytest.fixture
def archived_flow_cell() -> Path:
    """Path of archived flow cell"""
    return Path("/path/to/archived/run_devices.tar.gz.gpg")


@pytest.fixture
def archived_key() -> Path:
    """Path of archived key"""
    return Path("/path/to/archived/encryption_key.key.gpg")
