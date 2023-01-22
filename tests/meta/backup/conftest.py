from pathlib import Path

import pytest


@pytest.fixture(name="spring_file_path")
def fixture_spring_file_path() -> Path:
    """Return spring file path"""
    return Path("/path/to/spring_file.spring")


@pytest.fixture(name="backup_file_path")
def fixture_backup_file_path() -> str:
    """Return path to a file used in the backup process"""
    return "/path/to/backup_file.extension"


@pytest.fixture(name="archived_flow_cell")
def fixture_archived_flow_cell() -> Path:
    """Path of archived flow cell"""
    return Path("/path/to/archived/flow_cell.tar.gz.gpg")


@pytest.fixture(name="archived_key")
def fixture_archived_key() -> Path:
    """Path of archived key"""
    return Path("/path/to/archived/encryption_key.key.gpg")


@pytest.fixture(name="pdc_query")
def fixture_pdc_query() -> list:
    """Result of a PDC query"""
    return [
        "IBM Tivoli Storage Manager",
        "Command Line Backup-Archive Client Interface",
        "  Client Version 7, Release 1, Level 4.0 ",
        "  Client date/time: 05/15/2022 11:43:55",
        "(c) Copyright by IBM Corporation and other(s) 1990, 2015. All Rights Reserved.",
        "",
        "Node Name: HASTA.SCILIFELAB.SE_CLINICAL",
        "Session established with server BLACKHOLE: Linux/x86_64",
        "  Server Version 8, Release 1, Level 9.300",
        "  Server date/time: 05/15/2022 11:43:55  Last access: 05/15/2022 10:57:20",
        "",
        "Accessing as node: SLLCLINICAL",
        "             Size  Archive Date - Time    File - Expires on - Description",
        "             ----  -------------------    -------------------------------",
        "           607  B  03/28/2022 11:59:54    "
        "/path/to/archived/encryption_key.key.gpg Never "
        "Archive Date: 03/28/2022",
        "43,868,543,141  B  03/28/2022 11:53:04    "
        "/path/to/archived/flow_cell.tar.gz.gpg Never "
        "Archive Date: 03/28/2022",
    ]
