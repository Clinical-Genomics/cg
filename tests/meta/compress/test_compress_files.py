"""Tests for the compression files module"""
import logging
import os
from pathlib import Path

from cg.constants import FASTQ_FIRST_READ_SUFFIX, FASTQ_SECOND_READ_SUFFIX
from cg.meta.compress import files


def test_get_fastq_run_name():
    """Test to parse the run name of a fastq file"""
    # GIVEN a run name and a fastq file
    run = "run"
    fastq = Path(run + FASTQ_FIRST_READ_SUFFIX)

    # WHEN parsing the run name
    res = files.get_run_name(fastq)

    # THEN assert the name is the expected
    assert res == run


def test_get_fastq_run_name_real_file(fastq_files, sample):
    """Test to parse the run name of some existing fastq files"""
    # GIVEN a run name and a fastq file
    fastq_file = fastq_files["fastq_first_path"]
    assert fastq_file.exists()

    # WHEN parsing the run name
    res = files.get_run_name(fastq_file)

    # THEN assert the name is the expected
    assert res == sample


def test_get_individual_fastqs_one_run():
    """Test to get fastq files when there is one run"""
    # GIVEN a run with two fastqs
    run = "run"
    fastqs = [Path(run + FASTQ_FIRST_READ_SUFFIX), Path(run + FASTQ_SECOND_READ_SUFFIX)]

    # WHEN parsing the files
    individual_fastqs = files.get_fastq_runs(fastqs)

    # THEN assert that the run is returned
    assert run in individual_fastqs
    # THEN assert that the files are grouped under the run
    assert set(individual_fastqs[run]) == set(fastqs)


def test_get_individual_fastqs_multiple_runs():
    """Test to get fastq files when there are two runs"""
    # GIVEN a run with two fastqs
    run = "run"
    run_2 = "run_2"
    fastqs = [
        Path(run + FASTQ_FIRST_READ_SUFFIX),
        Path(run + FASTQ_SECOND_READ_SUFFIX),
        Path(run_2 + FASTQ_FIRST_READ_SUFFIX),
        Path(run_2 + FASTQ_SECOND_READ_SUFFIX),
    ]

    # WHEN parsing the files
    individual_fastqs = files.get_fastq_runs(fastqs)

    # THEN assert that both runs are returned
    assert run in individual_fastqs
    assert run_2 in individual_fastqs
    # THEN assert that the files are grouped under the run
    assert set(individual_fastqs[run]) == set(fastqs[:2])
    assert set(individual_fastqs[run_2]) == set(fastqs[2:])


def test_get_fastq_files(populated_compress_fastq_api, sample):
    """test get_fastq_files method when there are fastq files"""
    compress_api = populated_compress_fastq_api
    # GIVEN a sample_id and a hk api populated with fastq bundle

    # WHEN fetching the fastq files
    version_obj = compress_api.get_latest_version(sample)
    fastq_dict = files.get_fastq_files(sample_id=sample, version_obj=version_obj)
    run = list(fastq_dict.keys())[0]

    # THEN the fastq files will be in the dictionary
    assert set(fastq_dict[run].keys()) == set(["fastq_first_file", "fastq_second_file"])


def test_check_prefixes(sample):
    """test to check if two fastq files belong to the same readpair when they do"""

    # GIVEN two fatq files from the same readpair
    first_fastq = Path(sample) / FASTQ_FIRST_READ_SUFFIX
    second_fastq = Path(sample) / FASTQ_SECOND_READ_SUFFIX

    # WHEN checking if they belong to the same sample
    res = files.check_prefixes(first_fastq, second_fastq)

    # THEN assert that the result is true
    assert res is True


def test_get_fastq_files_no_files(compress_api, sample_hk_bundle_no_files, sample, helpers, caplog):
    """test get_fastq_files method when no files are found"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a sample_id
    sample_id = sample
    hk_api = compress_api.hk_api
    # GIVEN a bundle without files
    assert sample_hk_bundle_no_files["files"] == []
    helpers.ensure_hk_bundle(hk_api, sample_hk_bundle_no_files)

    # WHEN fetching the fastq files
    version_obj = compress_api.get_latest_version(sample)
    fastq_dict = files.get_fastq_files(sample_id=sample_id, version_obj=version_obj)

    # THEN assert that None is returned since there where not two files
    assert fastq_dict is None
    # THEN assert that the correct information is returned
    assert f"Could not find FASTQ files for {sample}" in caplog.text


def test_check_bam_path(bam_file):
    """Test the check bam file with an existing bam file"""
    # GIVEN an existing bam_path
    assert bam_file.exists()

    # WHEN checking the bam path in string format
    res = files.get_bam_path(str(bam_file), hk_files=[bam_file])

    # THEN assert that the file is returned as a path object
    assert res == bam_file


def test_get_bam_path_multiple_links(multi_linked_file, caplog):
    """Test to get the bam path when file have multiple links"""
    # GIVEN an file with multiple links
    assert os.stat(multi_linked_file).st_nlink > 1

    # WHEN checking the bam path in string format
    res = files.get_bam_path(str(multi_linked_file), hk_files=[multi_linked_file])

    # THEN assert that the file is returned as a path object
    assert res is None
    # THEN assert that the correct information is being processed
    assert "has more than 1 links to same inode" in caplog.text


def test_check_bam_path_not_in_hk(bam_file, caplog):
    """Test the get the bam path when it is not in the hk files"""
    # GIVEN an existing bam_path
    assert bam_file.exists()

    # WHEN checking the bam path in string format but not in hk_files
    res = files.get_bam_path(str(bam_file), hk_files=[])

    # THEN assert that None is returned
    assert res is None
    # THEN assert that the correct information is being processed
    assert f"{bam_file} not in latest version of housekeeper bundle" in caplog.text


def test_check_bam_file_wrong_suffix(bai_file, caplog):
    """Test the check bam file when the suffix is wrong"""
    # GIVEN an existing file that is not a bam file (not ends with .bam)
    assert bai_file.exists()

    # WHEN checking the bam path in string format
    res = files.get_bam_path(str(bai_file), hk_files=[bai_file])

    # THEN assert that None is returned
    assert res is None
    # THEN assert that the correct information is being communicated
    assert f"Alignment file does not have correct suffix .bam" in caplog.text


def test_check_bam_file_no_file(caplog):
    """Test the check bam file without None as argument"""
    # GIVEN a compress api

    # WHEN getting the bam path with None
    res = files.get_bam_path(None, hk_files=[])

    # THEN assert that the file is returned as a path object
    assert res is None
    # THEN assert that the correct information is being communicated
    assert f"No bam file found" in caplog.text


def test_check_bam_file_non_existing(bam_path):
    """Test the check bam file with a non existing bam file"""
    # GIVEN a non existing bam_path
    assert not bam_path.exists()

    # WHEN checking the bam path in string format
    res = files.get_bam_path(str(bam_path), hk_files=[bam_path])

    # THEN assert that None is returned
    assert res is None
