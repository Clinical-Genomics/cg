"""Test obseravtion input files"""
from pathlib import Path

import pytest


@pytest.fixture(name="file_does_not_exist")
def fixture_file_does_not_exist() -> Path:
    """Return a file path that does not exist"""
    return Path("dir", "does_not_really_exist")


@pytest.fixture(name="hk_tag")
def fixture_hk_tag() -> str:
    """Return a Housekeeper tag"""
    return "vcf"
