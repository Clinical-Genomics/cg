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
        log_dir=crunchy_config_dict["crunchy"]["slurm"]["log_dir"],
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
    # GIVEN a crunchy-api, and a bam_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = Path("/path/to/bam.bam")

    # WHEN checking if cram compression is done
    result = crunchy_api.cram_compression_done(bam_path=bam_path)

    # THEN result should be false
    assert not result


def test_cram_compression_done_no_crai(crunchy_config_dict, crunchy_test_dir):
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
