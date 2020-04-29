""" Tests for compress API """

import os
from pathlib import Path

from cg.apps.crunchy import CrunchyAPI
from cg.apps.scoutapi import ScoutAPI


def test_get_nlinks(compress_api, compress_test_dir):
    """Test get_nlinks"""
    # GIVEN a bam
    file_path = compress_test_dir / "file"
    file_path.touch()

    # WHEN getting number of links to inode
    nlinks = compress_api.get_nlinks(file_link=file_path)

    # THEN number of links should be one
    assert nlinks == 1

    # WHEN adding a link
    first_link = compress_test_dir / "link-1"
    os.link(file_path, first_link)
    nlinks = compress_api.get_nlinks(file_link=file_path)

    # THEN number of links should be two
    assert nlinks == 2

    # WHEN adding yet another link
    second_link = compress_test_dir / "link-2"
    os.link(file_path, second_link)
    nlinks = compress_api.get_nlinks(file_link=file_path)

    # THEN number of links should be three
    assert nlinks == 3


def test_get_bam_files(
    compress_api, compress_scout_case, compress_hk_bundle, case_id, mocker, helpers
):
    """test get_bam_files method"""

    # GIVEN a case id
    mocker.patch.object(ScoutAPI, "get_cases", return_value=[compress_scout_case])

    hk_api = compress_api.hk_api
    helpers.ensure_hk_bundle(hk_api, compress_hk_bundle)

    # WHEN getting bam-files
    bam_dict = compress_api.get_bam_files(case_id=case_id)

    # THEN the bam-files for the samples will be in the dictionary
    assert set(bam_dict.keys()) == set(["sample_1", "sample_2", "sample_3"])


def test_compress_case_bams(compress_api, bam_dict, mocker):
    """Test compress_case method"""
    # GIVEN a compress api and a bam dictionary
    mock_bam_to_cram = mocker.patch.object(CrunchyAPI, "bam_to_cram")

    # WHEN compressing the case
    compress_api.compress_case_bams(bam_dict=bam_dict, ntasks=1, mem=2)

    # THEN all samples in bam-files will have been compressed
    assert mock_bam_to_cram.call_count == len(bam_dict)


def test_update_scout(compress_api, bam_dict, mock_compress_func, mocker):
    """ Test update_hk method"""
    mock_compress_func(bam_dict)
    mock_update_alignment_file = mocker.patch.object(ScoutAPI, "update_alignment_file")
    # GIVEN a case-id
    case_id = "test_case"

    # WHEN updating scout
    compress_api.update_scout(case_id=case_id, bam_dict=bam_dict)

    # THEN update_alignment_file should have been callen three times
    assert mock_update_alignment_file.call_count == len(bam_dict)


def test_update_hk(compress_api, bam_dict, mock_compress_func):
    """ Test update_hk method"""
    mock_compress_func(bam_dict)
    hk_api = compress_api.hk_api
    # GIVEN a empty hk api
    assert len(hk_api.files()) == 0
    # GIVEN a case-id and a compress api
    case_id = "test-case"

    # WHEN updating hk
    compress_api.update_hk(case_id=case_id, bam_dict=bam_dict)

    # THEN add_file should have been called 6 times (two for every case)
    assert len(hk_api.files()) == 6


def test_remove_bams(compress_api, bam_dict, mock_compress_func):
    """ Test remove_bams method"""
    # GIVEN a bam-dict and a compress api
    compressed_dict = mock_compress_func(bam_dict)

    for _, files in compressed_dict.items():
        assert Path(files["bam"].full_path).exists()
        assert Path(files["bai"].full_path).exists()
        assert Path(files["cram"].full_path).exists()
        assert Path(files["crai"].full_path).exists()
        assert Path(files["flag"].full_path).exists()

    # WHEN calling remove_bams
    compress_api.remove_bams(bam_dict=bam_dict)

    # THEN the bam-files and flag-file should not exist

    for sample_id in compressed_dict:
        files = compressed_dict[sample_id]
        assert not Path(files["bam"].full_path).exists()
        assert not Path(files["bai"].full_path).exists()
        assert Path(files["cram"].full_path).exists()
        assert Path(files["crai"].full_path).exists()
        assert not Path(files["flag"].full_path).exists()


#######


def test_get_fastq_files_no_version(compress_api):
    """test get_fastq_files method when no version is found in hk"""

    # GIVEN a sample id
    sample_id = "test_sample"
    # GIVEN a hk_api that returns None for final version
    compress_api.hk_api._last_version = None

    # WHEN fetching fastq files
    fastq_dict = compress_api.get_fastq_files(sample_id=sample_id)

    # THEN assert that None was returned since there was no version object found
    assert fastq_dict is None


def test_get_fastq_files_no_files(compress_api, mocker):
    """test get_fastq_files method when no files are found"""

    # GIVEN a sample_id
    sample_id = "test_sample"
    # GIVEN a hk that returns an empty list of files
    mocker.patch.object(HousekeeperAPI, "get_files", return_value=[])

    # WHEN fetching the fastq files
    fastq_dict = compress_api.get_fastq_files(sample_id=sample_id)

    # THEN assert that None is returned since there where not two files
    assert fastq_dict is None


def test_get_fastq_files(compress_api, fastq_files_hk_list, mocker):
    """test get_fastq_files method"""

    # GIVEN a sample_id
    sample_id = "test_sample"
    mocker.patch.object(HousekeeperAPI, "get_files", return_value=fastq_files_hk_list)

    # WHEN fetching the fastq files
    fastq_dict = compress_api.get_fastq_files(sample_id=sample_id)

    # THEN the fastq files will be in the dictionary
    assert set(fastq_dict.keys()) == set(["fastq_first_file", "fastq_second_file"])
