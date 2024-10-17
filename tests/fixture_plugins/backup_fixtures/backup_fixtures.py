import fnmatch
from pathlib import Path
from typing import Callable

import pytest

from cg.constants import FileExtensions
from cg.meta.encryption.encryption import EncryptionAPI
from cg.meta.tar.tar import TarAPI
from cg.models.cg_config import CGConfig, PDCArchivingDirectory
from cg.services.illumina.backup.backup_service import IlluminaBackupService
from cg.services.pdc_service.pdc_service import PdcService
from cg.store.store import Store


@pytest.fixture
def mock_pdc_query_method(archived_illumina_runs: list[str]) -> Callable:
    """Returns a mock method mimicking the pattern search made by the dsmc q archive command."""

    def mock_method(search_pattern: str) -> list[str] | None:
        if match := fnmatch.filter(archived_illumina_runs, search_pattern):
            return match

    return mock_method


@pytest.fixture
def dsmc_q_archive_output() -> list[str]:
    output: str = """IBM Spectrum Protect
Command Line Backup-Archive Client Interface
  Client Version 8, Release 1, Level 11.0
  Client date/time: 09/16/2024 09:11:47
(c) Copyright by IBM Corporation and other(s) 1990, 2020. All Rights Reserved.

Node Name: INFINITE.IMPROBABILITY.DRIVE
Session established with server BLACKHOLE: Linux/x86_64
  Server Version 8, Release 1, Level 9.300
  Server date/time: 09/16/2024 09:11:48  Last access: 09/16/2024 09:11:19

Accessing as node: ArthurDent
             Size  Archive Date - Time    File - Expires on - Description
             ----  -------------------    -------------------------------
           607  B  12/03/2016 11:51:24    /home/hiseq.clinical/ENCRYPT/161115_ST-E00214_0117_BHVKJCDRXX.key.gpg Never Archive Date: 12/03/2016
   323,235,178  B  12/03/2016 11:51:18    /home/hiseq.clinical/ENCRYPT/161115_ST-E00214_0117_BHVKJCDRXX.tar.gz.gpg Never Archive Date: 12/03/2016
           607  B  12/03/2016 20:18:46    /home/hiseq.clinical/ENCRYPT/161115_ST-E00214_0118_BHVKJCDRXX.key.gpg Never Archive Date: 12/03/2016
   647,336,368 KB  12/03/2016 18:30:04    /home/hiseq.clinical/ENCRYPT/161115_ST-E00214_0118_BHVKJCDRXX.tar.gz.gpg Never Archive Date: 12/03/2016"""
    return output.splitlines()


@pytest.fixture
def archived_illumina_runs(pdc_archiving_directory: PDCArchivingDirectory) -> list[str]:
    """Returns a list of archived flow cells."""
    return [
        f"{pdc_archiving_directory.current}/new_flow_cell{FileExtensions.TAR}{FileExtensions.GZIP}{FileExtensions.GPG}",
        f"{pdc_archiving_directory.nas}/old_flow_cell{FileExtensions.TAR}{FileExtensions.GZIP}{FileExtensions.GPG}",
        f"{pdc_archiving_directory.pre_nas}/ancient_flow_cell{FileExtensions.TAR}{FileExtensions.GZIP}{FileExtensions.GPG}",
    ]


@pytest.fixture
def backup_api(
    cg_context: CGConfig, illumina_sequencing_runs_directory: Path
) -> IlluminaBackupService:
    """Return a BackupAPI instance."""
    encryption_api: EncryptionAPI = EncryptionAPI(
        binary_path=cg_context.encryption.binary_path, dry_run=True
    )
    store: Store = cg_context.status_db
    tar_api: TarAPI = TarAPI(binary_path=cg_context.tar.binary_path, dry_run=True)
    pdc_service: PdcService = PdcService(binary_path=cg_context.pdc.binary_path, dry_run=True)

    pdc_archiving_directory: PDCArchivingDirectory = (
        cg_context.illumina_backup_service.pdc_archiving_directory
    )
    _backup_api: IlluminaBackupService = IlluminaBackupService(
        encryption_api=encryption_api,
        status_db=store,
        tar_api=tar_api,
        pdc_service=pdc_service,
        pdc_archiving_directory=pdc_archiving_directory,
        sequencing_runs_dir=illumina_sequencing_runs_directory,
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
def archived_illumina_run() -> Path:
    """Path of archived sequencing run"""
    return Path("/path/to/archived/run_devices.tar.gz.gpg")


@pytest.fixture
def archived_key() -> Path:
    """Path of archived key"""
    return Path("/path/to/archived/encryption_key.key.gpg")
