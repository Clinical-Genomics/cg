"""Fixtures for compress api tests"""
import copy
import os
from pathlib import Path

import pytest

from cg.apps.crunchy import CrunchyAPI
from cg.constants import FASTQ_FIRST_READ_SUFFIX, FASTQ_SECOND_READ_SUFFIX
from cg.meta.compress import CompressAPI
from tests.mocks.hk_mock import MockFile


@pytest.yield_fixture(scope="function", name="compress_api")
def fixture_compress_api(crunchy_api, housekeeper_api, scout_api):
    """compress api fixture"""
    hk_api = housekeeper_api
    _api = CompressAPI(crunchy_api=crunchy_api, hk_api=hk_api, scout_api=scout_api)
    yield _api


@pytest.fixture(scope="function", name="populated_compress_api")
def fixture_populated_compress_api(
    compress_api, compress_scout_case, compress_hk_bam_bundle, helpers
):
    """Populated compress api fixture"""
    compress_api.scout_api.add_mock_case(compress_scout_case)
    helpers.ensure_hk_bundle(compress_api.hk_api, compress_hk_bam_bundle)

    return compress_api


@pytest.fixture(scope="function", name="populated_compress_fastq_api")
def fixture_populated_compress_fastq_api(
    compress_api, compress_scout_case, compress_hk_fastq_bundle, helpers
):
    """Populated compress api fixture"""
    compress_api.scout_api.add_mock_case(compress_scout_case)
    helpers.ensure_hk_bundle(compress_api.hk_api, compress_hk_fastq_bundle)

    return compress_api


@pytest.fixture(scope="function", name="sample")
def fixture_sample():
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


@pytest.fixture(scope="function", name="sample_dir")
def fixture_sample_dir(project_dir, sample) -> Path:
    """Return the path to a sample directory"""
    _dir = project_dir / sample
    _dir.mkdir(parents=True, exist_ok=True)
    return _dir


@pytest.fixture(scope="function", name="bam_path")
def fixture_bam_path(sample_dir) -> Path:
    """Return the path to a non existing bam file"""
    return sample_dir / "bam_1.bam"


@pytest.fixture(scope="function", name="bai_path")
def fixture_bai_path(sample_dir) -> Path:
    """Return the path to a non existing bam index file"""
    return sample_dir / "bam_1.bam.bai"


@pytest.fixture(scope="function", name="cram_path")
def fixture_cram_path(bam_path) -> Path:
    """Return the path to a non existing cram file"""
    return CrunchyAPI.get_cram_path_from_bam(bam_path=bam_path)


@pytest.fixture(scope="function", name="crai_path")
def fixture_crai_path(cram_path) -> Path:
    """Return the path to a non existing cram index file"""
    return CrunchyAPI.get_index_path(cram_path)["double_suffix"]


@pytest.fixture(scope="function", name="bam_flag_path")
def fixture_bam_flag_path(bam_path) -> Path:
    """Return the path to a non existing bam flag file"""
    return CrunchyAPI.get_flag_path(file_path=bam_path)


@pytest.fixture(scope="function", name="spring_path")
def fixture_spring_path(fastq_paths) -> Path:
    """Return the path to a non existing spring file"""
    return CrunchyAPI.get_spring_path_from_fastq(fastq=fastq_paths["fastq_first_path"])


@pytest.fixture(scope="function", name="fastq_flag_path")
def fixture_fastq_flag_path(spring_path) -> Path:
    """Return the path to a non existing fastq flag file"""
    return CrunchyAPI.get_flag_path(file_path=spring_path)


@pytest.fixture(scope="function", name="bam_file")
def fixture_bam_file(bam_path) -> Path:
    """Return the path to an existing bam file"""
    bam_path.touch()
    return bam_path


@pytest.fixture(scope="function", name="bai_file")
def fixture_bai_file(bai_path) -> Path:
    """Return the path to an existing bam index file"""
    bai_path.touch()
    return bai_path


@pytest.fixture(scope="function", name="cram_file")
def fixture_cram_file(cram_path) -> Path:
    """Return the path to an existing cram file"""
    cram_path.touch()
    return cram_path


@pytest.fixture(scope="function", name="crai_file")
def fixture_crai_file(crai_path) -> Path:
    """Return the path to an existing cram index file"""
    crai_path.touch()
    return crai_path


@pytest.fixture(scope="function", name="hk_bam_file")
def fixture_hk_bam_file(bam_file) -> Path:
    """Return a housekeeper file object"""
    return MockFile(path=str(bam_file))


@pytest.fixture(scope="function", name="hk_bai_file")
def fixture_hk_bai_file(bai_file) -> Path:
    """Return a housekeeper file object"""
    return MockFile(path=str(bai_file))


@pytest.fixture(scope="function", name="bam_flag_file")
def fixture_bam_flag_file(bam_flag_path) -> Path:
    """Return the path to an existing bam flag file"""
    bam_flag_path.touch()
    return bam_flag_path


@pytest.fixture(scope="function", name="fastq_flag_file")
def fixture_fastq_flag_file(fastq_flag_path) -> Path:
    """Return the path to an existing fastq flag file"""
    fastq_flag_path.touch()
    return fastq_flag_path


@pytest.fixture(scope="function", name="multi_linked_file")
def fixture_multi_linked_file(bam_file, project_dir) -> Path:
    """Return the path to an existing file with two links"""
    first_link = project_dir / "link-1"
    os.link(bam_file, first_link)

    return bam_file


@pytest.fixture(scope="function", name="bam_files")
def fixture_bam_files(project_dir, sample, sample_two, sample_three):
    """Fixture for temporary bam-files

    Creates files and return a dict will all files
    """
    sample_1_dir = project_dir / sample
    sample_1_dir.mkdir(parents=True, exist_ok=True)
    sample_2_dir = project_dir / sample_two
    sample_2_dir.mkdir(parents=True, exist_ok=True)
    sample_3_dir = project_dir / sample_three
    sample_3_dir.mkdir(parents=True, exist_ok=True)
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


@pytest.fixture(scope="function", name="fastq_paths")
def fixture_fastq_paths(project_dir, sample):
    """Fixture for temporary fastq-files

    Create fastq paths and return a dictionary with them
    """
    sample_dir = project_dir / sample
    sample_dir.mkdir(parents=True, exist_ok=True)
    fastq_first_file = sample_dir / f"{sample}{FASTQ_FIRST_READ_SUFFIX}"
    fastq_second_file = sample_dir / f"{sample}{FASTQ_SECOND_READ_SUFFIX}"
    fastq_first_file.touch()
    fastq_second_file.touch()

    return {
        "fastq_first_path": fastq_first_file,
        "fastq_second_path": fastq_second_file,
    }


@pytest.fixture(scope="function", name="fastq_files")
def fixture_fastq_files(fastq_paths):
    """Fixture for temporary fastq-files

    Create fastq files and return a dictionary with them
    """
    fastq_first_file = fastq_paths["fastq_first_path"]
    fastq_second_file = fastq_paths["fastq_second_path"]
    fastq_first_file.touch()
    fastq_second_file.touch()

    return fastq_paths


# Bundle fixtures


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


@pytest.fixture(scope="function", name="compress_hk_bam_bundle")
def fixture_compress_hk_bam_bundle(bam_files, case_hk_bundle_no_files):
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


@pytest.fixture(scope="function", name="compress_hk_bam_single_bundle")
def fixture_compress_hk_bam_single_bundle(bam_file, bai_file, case_hk_bundle_no_files):
    """Create a complete bundle mock for testing compression"""
    hk_bundle_data = copy.deepcopy(case_hk_bundle_no_files)

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


@pytest.fixture(scope="function", name="compress_scout_case")
def fixture_compress_scout_case(bam_files, case_id):
    """Fixture for scout case with bam-files"""
    case_data = {
        "_id": case_id,
        "individuals": [
            {"individual_id": sample, "bam_file": str(files["bam_file"])}
            for sample, files in bam_files.items()
        ],
    }
    return case_data
