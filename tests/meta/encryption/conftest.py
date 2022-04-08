from pathlib import Path

import pytest


@pytest.fixture(name="input_file")
def fixture_input_path() -> Path:
    """input file"""
    return Path("/path/to/input.file")


@pytest.fixture(name="output_file")
def fixture_output_path() -> Path:
    """output file"""
    return Path("/path/to/output.file")


@pytest.fixture(name="temporary_passphrase")
def fixture_temporary_passphrase() -> str:
    """temporary passphrase file"""
    return "tmp/tmp_test_passphrase"
