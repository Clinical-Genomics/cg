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
