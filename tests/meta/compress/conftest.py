"""Fixtures for compress api tests"""
import copy
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


@pytest.fixture(scope="function", name="sample")
def fixture_sample_one():
    """Return the sample id for first sample"""
    return "sample_1"


@pytest.fixture(scope="function", name="sample_two")
def fixture_sample_two():
    """Return the sample id for second sample"""
    return "sample_2"


@pytest.fixture(scope="function", name="sample_three")
def fixture_sample_three():
    """Return the sample id for third sample"""
    return "sample_3"


@pytest.fixture(scope="function", name="bam_files")
def fixture_bam_files(project_dir, sample, sample_two, sample_three):
    """Fixture for temporary bam-files

    Creates files and return a dict will all files
    """
    sample_1_dir = project_dir / sample
    sample_1_dir.mkdir()
    sample_2_dir = project_dir / sample_two
    sample_2_dir.mkdir()
    sample_3_dir = project_dir / sample_three
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
        sample: {"bam_file": bam_file_1, "bai_file": bai_file_1},
        sample_two: {"bam_file": bam_file_2, "bai_file": bai_file_2},
        sample_three: {"bam_file": bam_file_3, "bai_file": bai_file_3},
    }


@pytest.fixture(scope="function", name="fastq_files")
def fixture_fastq_files(project_dir, sample):
    """Fixture for temporary fastq-files

    Create fastq files and return a dictionary with them
    """
    sample_1_dir = project_dir / sample
    sample_1_dir.mkdir()
    fastq_first_file = sample_1_dir / f"sample{FASTQ_FIRST_READ_SUFFIX}"
    fastq_second_file = sample_1_dir / f"sample{FASTQ_SECOND_READ_SUFFIX}"
    fastq_first_file.touch()
    fastq_second_file.touch()

    return {
        "fastq_first_path": fastq_first_file,
        "fastq_second_path": fastq_second_file,
    }


@pytest.fixture(scope="function", name="sample_hk_bundle_no_files")
def fixture_sample_hk_bundle_no_files(sample, timestamp):
    """Create a complete bundle mock for testing compression"""
    hk_bundle_data = {
        "name": sample,
        "created": timestamp,
        "expires": timestamp,
        "files": [],
    }

    return hk_bundle_data


@pytest.fixture(scope="function", name="case_hk_bundle_no_files")
def fixture_case_hk_bundle_no_files(case_id, timestamp):
    """Create a complete bundle mock for testing compression"""
    hk_bundle_data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [],
    }

    return hk_bundle_data


@pytest.fixture(scope="function")
def compress_hk_bam_bundle(bam_files, case_hk_bundle_no_files):
    """Create a complete bundle mock for testing compression"""
    hk_bundle_data = copy.deepcopy(case_hk_bundle_no_files)

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


@pytest.fixture(scope="function", name="compress_hk_fastq_bundle")
def fixture_compress_hk_fastq_bundle(fastq_files, sample_hk_bundle_no_files):
    """Create a complete bundle mock for testing compression"""
    hk_bundle_data = copy.deepcopy(sample_hk_bundle_no_files)

    first_fastq = fastq_files["fastq_first_path"]
    second_fastq = fastq_files["fastq_second_path"]
    for fastq_file in [first_fastq, second_fastq]:
        fastq_file_info = {"path": str(fastq_file), "archive": False, "tags": ["fastq"]}

        hk_bundle_data["files"].append(fastq_file_info)

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
    case_data = {
        "_id": case_id,
        "individuals": [
            {"individual_id": sample, "bam_file": str(files["bam_file"])}
            for sample, files in bam_files.items()
        ],
    }
    return case_data


@pytest.fixture(scope="function", name="bam_dict")
def fixture_bam_dict(bam_files):
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
