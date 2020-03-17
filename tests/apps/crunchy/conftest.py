import pytest
import shutil
from pathlib import Path


@pytest.fixture(scope="function")
def crunchy_test_dir(tmpdir_factory):
    """Path to a temporary directory"""
    my_tmpdir = Path(tmpdir_factory.mktemp("data"))
    yield my_tmpdir
    shutil.rmtree(str(my_tmpdir))


@pytest.fixture(scope="function")
def mock_bam_to_cram():
    """ This fixture returns a mocked bam_to_cram method. this mock_method
        Will create files with suffixes .cram and .crai for a given BAM path"""

    def _mock_bam_to_cram_func(
        bam_path: Path, ntasks: int, mem: int, dry_run: bool = False
    ):

        _ = dry_run
        _ = ntasks
        _ = mem

        cram_path = bam_path.with_suffix(".cram")
        crai_path = bam_path.with_suffix(".cram.crai")
        flag_path = bam_path.with_suffix(".crunchy.txt")

        cram_path.touch()
        crai_path.touch()
        flag_path.touch()

    return _mock_bam_to_cram_func
