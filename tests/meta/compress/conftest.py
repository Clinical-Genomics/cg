"""Fixtures for compress api tests"""
import shutil
from pathlib import Path

import pytest

from cg.apps.crunchy import CrunchyAPI
from cg.apps.scoutapi import ScoutAPI
from cg.constants import FASTQ_FIRST_READ_SUFFIX, FASTQ_SECOND_READ_SUFFIX
from cg.meta.compress import CompressAPI
from tests.mocks.hk_mock import MockFile


class MockScout(ScoutAPI):
    """Mock class for Scout api"""

    def __init__(self):
        pass


class MockCrunchy(CrunchyAPI):
    """Mock crunchy api"""


@pytest.yield_fixture(scope="function", name="crunchy_api")
def fixture_crunchy_api(crunchy_config_dict):
    """crunchy api fixture"""
    _api = MockCrunchy(crunchy_config_dict)
    yield _api


@pytest.yield_fixture(scope="function")
def compress_api(crunchy_api, housekeeper_api):
    """compress api fixture"""
    hk_api = housekeeper_api
    scout_api = MockScout()
    _api = CompressAPI(crunchy_api=crunchy_api, hk_api=hk_api, scout_api=scout_api)
    yield _api


@pytest.fixture(scope="function")
def compress_test_dir(tmpdir_factory):
    """Path to a temporary directory"""
    my_tmpdir = Path(tmpdir_factory.mktemp("data"))
    yield my_tmpdir
    shutil.rmtree(str(my_tmpdir))


@pytest.fixture(scope="function", name="bam_files")
def fixture_bam_files(compress_test_dir):
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
def fastq_files(compress_test_dir):
    """Fixture for temporary fastq-files"""
    sample_1_dir = compress_test_dir / "sample_1"
    sample_1_dir.mkdir()
    fastq_first_file = sample_1_dir / f"sample{FASTQ_FIRST_READ_SUFFIX}"
    fastq_second_file = sample_1_dir / f"sample{FASTQ_SECOND_READ_SUFFIX}"
    fastq_first_file.touch()
    fastq_second_file.touch()

    return {
        "fastq_first_path": fastq_first_file,
        "fastq_second_path": fastq_second_file,
    }


@pytest.fixture(scope="function")
def compress_hk_bundle(bam_files, case_id, timestamp):
    """hk file list fixture"""
    hk_bundle_data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [],
    }
    for sample_id in bam_files:
        bam_file = bam_files[sample_id]["bam_file"]
        bai_file = bam_files[sample_id]["bai_file"]
        bam_file_info = {"path": str(bam_file), "archive": False, "tags": ["bam"]}
        bai_file_info = {
            "path": str(bai_file),
            "archive": False,
            "tags": ["bai", "bam-index"],
        }
        hk_bundle_data["files"].append(bam_file_info)
        hk_bundle_data["files"].append(bai_file_info)

    return hk_bundle_data


@pytest.fixture(scope="function")
def fastq_files_hk_list(fastq_files):
    """hk file list fixture"""
    _hk_fastq_list = []

    for _, fastq_file in fastq_files.items():
        _hk_fastq_list.append(MockFile(path=fastq_file))

    return _hk_fastq_list


@pytest.fixture(scope="function")
def compress_scout_case(bam_files, case_id):
    """Fixture for scout case with bam-files"""
    return {
        "_id": case_id,
        "individuals": [
            {"individual_id": sample, "bam_file": str(files["bam_file"])}
            for sample, files in bam_files.items()
        ],
    }


@pytest.fixture(scope="function")
def bam_dict(bam_files):
    """bam_dict fixture"""
    _bam_dict = {}
    for sample, files in bam_files.items():
        _bam_dict[sample] = {
            "bam": MockFile(path=files["bam_file"]),
            "bai": MockFile(path=files["bai_file"]),
        }
    return _bam_dict


@pytest.fixture(scope="function")
def mock_compress_func():
    """fixture with function that mocks a CRAM compression of bam_dict"""

    def _mock_compress_func(bam_dict: dict):
        """Creates corresponding .cram, .crai and flag path for BAM files"""
        _bam_dict = {}
        for sample, files in bam_dict.items():
            bam_path = Path(files["bam"].full_path)
            cram_path = bam_path.with_suffix(".cram")
            crai_path = bam_path.with_suffix(".cram.crai")
            flag_path = bam_path.with_suffix(".crunchy.txt")
            cram_path.touch()
            crai_path.touch()
            flag_path.touch()

            _bam_dict[sample] = {
                "bam": files["bam"],
                "bai": files["bai"],
                "cram": MockFile(path=str(cram_path)),
                "crai": MockFile(path=str(crai_path)),
                "flag": MockFile(path=str(flag_path)),
            }

        return _bam_dict

    return _mock_compress_func
