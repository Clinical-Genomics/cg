import pytest
import shutil
from pathlib import Path

from cg.apps.scoutapi import ScoutAPI
from cg.apps.hk import HousekeeperAPI
from cg.apps.crunchy import CrunchyAPI
from cg.meta.compress import CompressAPI


class MockScout(ScoutAPI):
    """Mock class for Scout api"""

    def __init__(self):
        pass


class MockVersion:
    def __init__(self):
        self.id = 1


class MockHousekeeper(HousekeeperAPI):
    """mock hk api"""

    def __init__(self):
        pass

    def last_version(self, bundle):
        _ = bundle
        return MockVersion()


class MockCrunchy(CrunchyAPI):

    pass


class MockFile:
    """Mock a file object"""

    def __init__(self, path="", to_archive=False):
        self.path = path
        self.to_archive = to_archive

    @property
    def full_path(self):
        return str(self.path)

    def is_included(self):
        return False


@pytest.yield_fixture(scope="function")
def crunchy_api(crunchy_config_dict):

    _api = MockCrunchy(crunchy_config_dict)
    yield _api


@pytest.yield_fixture(scope="function")
def compress_api(crunchy_api):

    hk_api = MockHousekeeper()
    scout_api = MockScout()
    _api = CompressAPI(crunchy_api=crunchy_api, hk_api=hk_api, scout_api=scout_api)
    yield _api


@pytest.fixture(scope="function")
def compress_test_dir(tmpdir_factory):
    """Path to a temporary directory"""
    my_tmpdir = Path(tmpdir_factory.mktemp("data"))
    yield my_tmpdir
    shutil.rmtree(str(my_tmpdir))


@pytest.fixture(scope="function")
def bam_files(compress_test_dir):
    """Fixture for temporary bam-files"""
    sample_1_dir = compress_test_dir / "sample_1"
    sample_1_dir.mkdir()
    sample_2_dir = compress_test_dir / "sample_2"
    sample_2_dir.mkdir()
    sample_3_dir = compress_test_dir / "sample_3"
    sample_3_dir.mkdir()
    bam_file_1 = sample_1_dir / "bam_1.bam"
    bai_file_1 = sample_1_dir / "bam_1.bam.bai"
    bam_file_2 = sample_2_dir / "bam_2.bam"
    bai_file_2 = sample_2_dir / "bam_2.bam.bai"
    bam_file_3 = sample_3_dir / "bam_3.bam"
    bai_file_3 = sample_3_dir / "bam_3.bam.bai"
    bam_file_1.touch()
    bai_file_1.touch()
    bam_file_2.touch()
    bai_file_2.touch()
    bam_file_3.touch()
    bai_file_3.touch()

    return {
        "sample_1": {"bam_file": bam_file_1, "bai_file": bai_file_1},
        "sample_2": {"bam_file": bam_file_2, "bai_file": bai_file_2},
        "sample_3": {"bam_file": bam_file_3, "bai_file": bai_file_3},
    }


@pytest.fixture(scope="function")
def bam_files_hk_list(bam_files):

    _hk_bam_list = []

    for _, bam_files in bam_files.items():
        _hk_bam_list.append(MockFile(path=bam_files["bam_file"]))
        _hk_bam_list.append(MockFile(path=bam_files["bai_file"]))

    return _hk_bam_list


@pytest.fixture(scope="function")
def compress_scout_case(bam_files):
    """Fixture for scout case with bam-files"""
    return {
        "_id": "test_case",
        "individuals": [
            {"individual_id": sample, "bam_file": str(files["bam_file"])}
            for sample, files in bam_files.items()
        ],
    }
