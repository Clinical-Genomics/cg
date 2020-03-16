"""Tests for CrunchyAPI"""

import pytest
from pathlib import Path

from cg.apps.crunchy import CrunchyAPI
from cg.apps.crunchy import SBATCH_HEADER_TEMPLATE, SBATCH_BAM_TO_CRAM, FLAG_PATH_SUFFIX
from cg.apps.constants import (
    BAM_SUFFIX,
    BAM_INDEX_SUFFIX,
    CRAM_SUFFIX,
    CRAM_INDEX_SUFFIX,
    FASTQ_FIRST_SUFFIX,
    FASTQ_SECOND_SUFFIX,
    SPRING_SUFFIX,
)


def test_bam_to_cram(crunchy_config_dict, mocker):
    """test bam_to_cram method"""
    # GIVEN a crunchy-api, and a bam_path
    mocker_submit_sbatch = mocker.patch.object(CrunchyAPI, "_submit_sbatch")
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = Path("/path/to/bam.bam")
    # WHEN calling bam_to_cram method on bam-path
    crunchy_api.bam_to_cram(bam_path=bam_path, dry_run=False)
    # THEN _submit_sbatch method is called with correct sbatch-content
    sbatch_header = SBATCH_HEADER_TEMPLATE.format(
        job_name=bam_path.name + "_bam_to_cram",
        account=crunchy_config_dict["crunchy"]["slurm"]["account"],
        log_dir=bam_path.parent,
        mail_user=crunchy_config_dict["crunchy"]["slurm"]["mail_user"],
        crunchy_env=crunchy_config_dict["crunchy"]["slurm"]["conda_env"],
    )

    sbatch_bam_to_cram = SBATCH_BAM_TO_CRAM.format(
        reference_path=crunchy_config_dict["crunchy"]["cram_reference"],
        bam_path=bam_path,
        cram_path=bam_path.with_suffix(".cram"),
        flag_path=bam_path.with_suffix(FLAG_PATH_SUFFIX),
    )

    expected_sbatch_content = "\n".join([sbatch_header, sbatch_bam_to_cram])
    mocker_submit_sbatch.assert_called_with(
        sbatch_content=expected_sbatch_content, dry_run=False
    )


def test_cram_compression_done_no_cram(crunchy_config_dict):
    """test cram_compression_done without created cram file"""
    # GIVEN a crunchy-api, and a bam_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = Path("/path/to/bam.bam")

    # WHEN checking if cram compression is done
    result = crunchy_api.cram_compression_done(bam_path=bam_path)

    # THEN result should be false
    assert not result


def test_cram_compression_done_no_crai(crunchy_config_dict, crunchy_test_dir):
    """test cram_compression_done without created crai file"""
    # GIVEN a crunchy-api, and a bam_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = crunchy_test_dir / "file.bam"
    cram_path = crunchy_test_dir / "file.cram"
    flag_path = crunchy_test_dir / "file.crunchy.txt"
    bam_path.touch()
    cram_path.touch()
    flag_path.touch()
    assert bam_path.exists()
    assert cram_path.exists()
    assert flag_path.exists()
    # WHEN checking if cram compression is done
    result = crunchy_api.cram_compression_done(bam_path=bam_path)

    # THEN result should be false
    assert not result


def test_cram_compression_done_no_flag(crunchy_config_dict, crunchy_test_dir):
    """test cram_compression_done without created flag file"""
    # GIVEN a crunchy-api, and a bam_path, cram_path, crai_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = crunchy_test_dir / "file.bam"
    cram_path = crunchy_test_dir / "file.cram"
    crai_path = crunchy_test_dir / "file.cram.crai"
    bam_path.touch()
    cram_path.touch()
    crai_path.touch()
    assert bam_path.exists()
    assert cram_path.exists()
    assert crai_path.exists()
    # WHEN checking if cram compression is done
    result = crunchy_api.cram_compression_done(bam_path=bam_path)

    # THEN result should be False
    assert not result


def test_cram_compression_done(crunchy_config_dict, crunchy_test_dir):
    """test cram_compression_done with created cram, crai, and flag files"""
    # GIVEN a crunchy-api, and a bam_path, cram_path, crai_path, and flag_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = crunchy_test_dir / "file.bam"
    cram_path = crunchy_test_dir / "file.cram"
    crai_path = crunchy_test_dir / "file.cram.crai"
    flag_path = crunchy_test_dir / "file.crunchy.txt"
    bam_path.touch()
    cram_path.touch()
    crai_path.touch()
    flag_path.touch()
    assert bam_path.exists()
    assert cram_path.exists()
    assert crai_path.exists()
    assert flag_path.exists()
    # WHEN checking if cram compression is done
    result = crunchy_api.cram_compression_done(bam_path=bam_path)

    # THEN result should be True
    assert result


def test_cram_compression_before_after(
    crunchy_config_dict, crunchy_test_dir, mock_bam_to_cram, mocker
):
    """test cram_compression_done without before and after creating files"""
    # GIVEN a crunchy-api, and a bam_path
    bam_path = Path(crunchy_test_dir / "file.bam")
    mocker.patch.object(CrunchyAPI, "bam_to_cram", side_effect=mock_bam_to_cram)
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    # WHEN calling cram_compression_done on bam_path
    result = crunchy_api.cram_compression_done(bam_path=bam_path)
    # Cram compression is not done
    assert not result
    # GIVEN created cram, crai, and flag paths
    crunchy_api.bam_to_cram(bam_path=bam_path, dry_run=False)
    # WHEN calling cram_compression_done on bam_path
    result = crunchy_api.cram_compression_done(bam_path=bam_path)
    # THEN compression is marked as done
    assert result


def test_bam_compression_possible_no_bam(crunchy_config_dict, crunchy_test_dir):
    """test bam_compression_possible for non-existing bam"""
    # GIVEN a bam path to non existing file and a crunchy api
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = crunchy_test_dir / "file.bam"

    # WHEN calling test_bam_compression_possible
    result = crunchy_api.bam_compression_possible(bam_path=bam_path)

    # THEN this should return False
    assert not result


def test_bam_compression_possible_cram_done(
    crunchy_config_dict, crunchy_test_dir, mock_bam_to_cram, mocker
):
    """test bam_compression_possible for existing compression"""
    # GIVEN a bam path to a existing file and a crunchy api
    mocker.patch.object(CrunchyAPI, "bam_to_cram", side_effect=mock_bam_to_cram)
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = crunchy_test_dir / "file.bam"
    bam_path.touch()

    # WHEN calling test_bam_compression_possible when cram_compression is done
    crunchy_api.bam_to_cram(bam_path=bam_path, dry_run=False)
    result = crunchy_api.bam_compression_possible(bam_path=bam_path)

    # THEN this should return False
    assert not result


def test_bam_compression_possible(crunchy_config_dict, crunchy_test_dir):
    """test bam_compression_possible compressable bam"""
    # GIVEN a bam path to existing file and a crunchy api
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = crunchy_test_dir / "file.bam"
    bam_path.touch()

    # WHEN calling test_bam_compression_possible
    result = crunchy_api.bam_compression_possible(bam_path=bam_path)

    # THEN this will return True
    assert result


def test_get_flag_path(crunchy_config_dict, crunchy_test_dir):
    """test get_flag_path"""

    # GIVEM a bam_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = crunchy_test_dir / "file.bam"

    # WHEN creating flag path
    flag_path = crunchy_api.get_flag_path(file_path=bam_path)

    # THEN this should replace current suffix with FLAG_PATH_SUFFIX
    assert flag_path.suffixes == [".crunchy", ".txt"]


def test_get_index_path(crunchy_config_dict, crunchy_test_dir):
    """test get_index_path"""

    # GIVEM a bam_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = crunchy_test_dir / "file.bam"

    # WHEN creating bam path
    bai_path = crunchy_api.get_index_path(file_path=bam_path)

    # THEN this should replace current suffix with .bam.bai
    assert bai_path.suffixes == [".bam", ".bai"]

    # GIVEM a bam_path
    cram_path = crunchy_test_dir / "file.cram"

    # WHEN creating flag path
    crai_path = crunchy_api.get_index_path(file_path=cram_path)

    # THEN this should replace current suffix with .cram.crai
    assert crai_path.suffixes == [".cram", ".crai"]


def test_change_suffix_bam_to_cram(crunchy_config_dict, crunchy_test_dir):
    """test change_suffic_bam_to_cram"""
    # GIVEM a bam_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = crunchy_test_dir / "file.bam"

    # WHEN changing suffix to cram
    cram_path = crunchy_api.change_suffix_bam_to_cram(bam_path=bam_path)

    # THEN suffix should be .cram
    assert cram_path.suffix == CRAM_SUFFIX
