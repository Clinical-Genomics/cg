"""Tests for bam part of meta compress api"""

from pathlib import Path

from cg.apps.crunchy import CrunchyAPI
from cg.apps.scoutapi import ScoutAPI


def test_get_bam_files(
    compress_api, compress_scout_case, compress_hk_bam_bundle, case_id, mocker, helpers
):
    """test get_bam_files method"""

    # GIVEN a case id
    mocker.patch.object(ScoutAPI, "get_cases", return_value=[compress_scout_case])

    hk_api = compress_api.hk_api
    helpers.ensure_hk_bundle(hk_api, compress_hk_bam_bundle)

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
