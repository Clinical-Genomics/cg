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


@pytest.fixture(name="binary_path")
def fixture_binary_path() -> str:
    """Return the string of a path to a binary"""
    return "/usr/bin/binary"
