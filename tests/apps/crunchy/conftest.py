import pytest
import shutil
from pathlib import Path


@pytest.fixture(scope="function")
def crunchy_test_dir(tmpdir_factory):
    """Path to a temporary directory"""
    my_tmpdir = Path(tmpdir_factory.mktemp("data"))
    yield my_tmpdir
    shutil.rmtree(str(my_tmpdir))
