"""Tests for compress bam methods"""

import pytest

from cg.apps.crunchy import CrunchyAPI


def test_bamcompression_pending_with_flag(crunchy_config_dict, bam_path):
    """Test the method that checks if cram compression is pending.

    In this case there WILL be a flag (pending_path) so the method should return True.
    This means that the compression is not ready
    """
    # GIVEN a crunchy-api, and a bam_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN that the flag exists
    flag_path = crunchy_api.get_pending_path(file_path=bam_path)
    flag_path.touch()
    assert flag_path.exists()

    # WHEN calling the function to check if compression is pending
    result = crunchy_api.is_compression_pending(bam_path)

    # THEN the function should return True since the flag exists
    assert result is True


def test_bamcompression_pending_no_flag(crunchy_config_dict, bam_path):
    """Test the method that checks if cram compression is pending.

    In this case there will not be a flag (pending_path) so the method should return False
    """
    # GIVEN a crunchy-api, and a bam_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # GIVEN that the flag does not exist
    flag_path = crunchy_api.get_pending_path(file_path=bam_path)
    assert flag_path.exists() is False

    # WHEN calling the function to check if compression is pending
    result = crunchy_api.is_compression_pending(bam_path)

    # THEN the function should return False
    assert result is False


def test_get_crampath_from_cram_wrong_suffix(crunchy_config_dict, bam_path):
    """Test to build a cream path from a bam path when the suffix is wrong

    Since the method will realise this is not a bam path a ValueError will be raised
    """
    # GIVEN a crunchy-api, and a bam_path with wrong suffix
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    new_file = bam_path.with_suffix(".fastq")

    # WHEN calling the method to create a bam path
    with pytest.raises(ValueError):
        # THEN a ValueError should be raised since the file does not have a valid bam file suffix
        crunchy_api.get_cram_path_from_bam(bam_path=new_file)


def test_bam_to_cram(crunchy_config_dict, sbatch_content, bam_path, mocker):
    """Test bam_to_cram method

    Test to compress bam to cram method. This test will make sure that the correct sbatch content
    was submitted to the Process api
    """
    # GIVEN a crunchy-api, and a bam_path
    mocker_submit_sbatch = mocker.patch.object(CrunchyAPI, "_submit_sbatch")
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    log_path = crunchy_api.get_log_dir(bam_path)
    sbatch_path = crunchy_api.get_sbatch_path(log_path, "bam")

    # WHEN calling bam_to_cram method on bam-path
    crunchy_api.bam_to_cram(bam_path=bam_path)

    # THEN _submit_sbatch method is called with expected sbatch-content

    mocker_submit_sbatch.assert_called_with(sbatch_content=sbatch_content, sbatch_path=sbatch_path)
