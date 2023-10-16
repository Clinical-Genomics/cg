import fnmatch
import subprocess
from pathlib import Path
from typing import Callable, List

import pytest

from cg.constants.pdc import PDCExitCodes
from cg.models.cg_config import EncryptionDirectories


@pytest.fixture
def dummy_pdc_query_method(archived_flow_cells) -> Callable:
    def dummy_method(search_pattern: str) -> list[str]:
        match = fnmatch.filter(archived_flow_cells, search_pattern)
        if not match:
            raise subprocess.CalledProcessError(
                cmd="dummy_method", returncode=PDCExitCodes.NO_FILES_FOUND
            )
        return match

    return dummy_method


@pytest.fixture
def dsmc_q_archive_output() -> List[str]:
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


def construct_dsmc_q_archive_output(flow_cell_path: Path) -> str:
    output: str = f"""IBM Tivoli Storage Manager
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
           607  B  04/07/2019 07:30:15    {flow_cell_path.with_suffix(".key.gpg")} Never Archive Date: 04/07/2019
 1,244,997,334 KB  04/07/2019 04:00:05    {flow_cell_path.with_suffix(".tar.gz.gpg")} Never Archive Date: 04/07/2019"""
    return output


@pytest.fixture()
def archived_flow_cells(encryption_directories: EncryptionDirectories) -> list[str]:
    return [
        f"{encryption_directories.current}/new_flow_cell.gpg",
        f"{encryption_directories.nas}/old_flow_cell.gpg",
        f"{encryption_directories.pre_nas}/really_old_flow_cell.gpg",
    ]


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
    return Path("/path/to/archived/flow_cell.tar.gz.gpg")


@pytest.fixture
def archived_key() -> Path:
    """Path of archived key"""
    return Path("/path/to/archived/encryption_key.key.gpg")
