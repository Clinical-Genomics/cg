"""Tests for CrunchyAPI"""

from pathlib import Path

from cg.apps.crunchy import CrunchyAPI
from cg.constants import (CRAM_SUFFIX, FASTQ_FIRST_READ_SUFFIX,
                          FASTQ_SECOND_READ_SUFFIX)


def test_bam_to_cram(crunchy_config_dict, sbatch_content, bam_path, mocker):
    """Test bam_to_cram method"""
    # GIVEN a crunchy-api, and a bam_path
    mocker_submit_sbatch = mocker.patch.object(CrunchyAPI, "_submit_sbatch")
    crunchy_api = CrunchyAPI(crunchy_config_dict)

    # WHEN calling bam_to_cram method on bam-path
    crunchy_api.bam_to_cram(bam_path=bam_path, dry_run=False, ntasks=1, mem=2)

    # THEN _submit_sbatch method is called with expected sbatch-content

    mocker_submit_sbatch.assert_called_with(
        sbatch_content=sbatch_content, dry_run=False
    )


def test_is_cram_compression_done_no_cram(crunchy_config_dict, bam_path):
    """test cram_compression_done without created CRAM file"""
    # GIVEN a crunchy-api, and a bam_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)

    # WHEN checking if cram compression is done
    result = crunchy_api.is_cram_compression_done(bam_path=bam_path)

    # THEN result should be false
    assert not result


def test_is_cram_compression_done_no_crai(
    crunchy_config_dict, compressed_bam_without_crai
):
    """test cram_compression_done without created CRAI file"""
    # GIVEN a crunchy-api, and a bam_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = compressed_bam_without_crai

    # WHEN checking if cram compression is done
    result = crunchy_api.is_cram_compression_done(bam_path=bam_path)

    # THEN result should be false
    assert not result


def test_is_cram_compression_done_no_flag(
    crunchy_config_dict, compressed_bam_without_flag
):
    """test cram_compression_done without created flag file"""
    # GIVEN a crunchy-api, and a bam_path, cram_path, crai_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = compressed_bam_without_flag

    # WHEN checking if cram compression is done
    result = crunchy_api.is_cram_compression_done(bam_path=bam_path)

    # THEN result should be False
    assert not result


def test_is_cram_compression_done(crunchy_config_dict, compressed_bam):
    """Test cram_compression_done with created CRAM, CRAI, and flag files"""
    # GIVEN a crunchy-api, and a bam_path, cram_path, crai_path, and flag_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = compressed_bam

    # WHEN checking if cram compression is done
    result = crunchy_api.is_cram_compression_done(bam_path=bam_path)

    # THEN result should be True
    assert result


def test_cram_compression_before_after(
    crunchy_config_dict, crunchy_test_dir, mock_bam_to_cram, mocker
):
    """Test cram_compression_done without before and after creating files"""
    # GIVEN a crunchy-api, and a bam_path
    bam_path = Path(crunchy_test_dir / "file.bam")
    mocker.patch.object(CrunchyAPI, "bam_to_cram", side_effect=mock_bam_to_cram)
    crunchy_api = CrunchyAPI(crunchy_config_dict)

    # WHEN calling cram_compression_done on bam_path
    result = crunchy_api.is_cram_compression_done(bam_path=bam_path)

    # Cram compression is not done
    assert not result

    # GIVEN created cram, crai, and flag paths
    crunchy_api.bam_to_cram(bam_path=bam_path, dry_run=False, ntasks=1, mem=2)

    # WHEN calling cram_compression_done on bam_path
    result = crunchy_api.is_cram_compression_done(bam_path=bam_path)

    # THEN compression is marked as done
    assert result


def test_is_bam_compression_possible_no_bam(crunchy_config_dict, bam_path):
    """Test bam_compression_possible for non-existing BAM"""
    # GIVEN a bam path to non existing file and a crunchy api
    crunchy_api = CrunchyAPI(crunchy_config_dict)

    # WHEN calling test_bam_compression_possible
    result = crunchy_api.is_bam_compression_possible(bam_path=bam_path)

    # THEN this should return False
    assert not result


def test_is_bam_compression_possible_cram_done(
    crunchy_config_dict, crunchy_test_dir, mock_bam_to_cram, mocker
):
    """Test bam_compression_possible for existing compression"""
    # GIVEN a bam path to a existing file and a crunchy api
    mocker.patch.object(CrunchyAPI, "bam_to_cram", side_effect=mock_bam_to_cram)
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = crunchy_test_dir / "file.bam"
    bam_path.touch()

    # WHEN calling test_bam_compression_possible when cram_compression is done
    crunchy_api.bam_to_cram(bam_path=bam_path, dry_run=False, ntasks=1, mem=2)
    result = crunchy_api.is_bam_compression_possible(bam_path=bam_path)

    # THEN this should return False
    assert not result


def test_is_bam_compression_possible(crunchy_config_dict, crunchy_test_dir):
    """Test bam_compression_possible compressable BAM"""
    # GIVEN a bam path to existing file and a crunchy api
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = crunchy_test_dir / "file.bam"
    bam_path.touch()

    # WHEN calling test_bam_compression_possible
    result = crunchy_api.is_bam_compression_possible(bam_path=bam_path)

    # THEN this will return True
    assert result


def test_get_flag_path_bam(crunchy_config_dict, crunchy_test_dir):
    """Test get_flag_path for a bam file"""

    # GIVEN a bam_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = crunchy_test_dir / "file.bam"

    # WHEN creating flag path
    flag_path = crunchy_api.get_flag_path(file_path=bam_path)

    # THEN this should replace current suffix with FLAG_PATH_SUFFIX
    assert flag_path.suffixes == [".crunchy", ".txt"]


def test_get_flag_path_spring(crunchy_config_dict, crunchy_test_dir):
    """Test get_flag_path for a spring file"""

    # GIVEN a spring path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    spring_path = crunchy_test_dir / "file.spring"

    # WHEN creating flag path
    flag_path = crunchy_api.get_flag_path(file_path=spring_path)

    # THEN this file should have a json prefix
    assert flag_path.suffixes == [".json"]


def test_get_index_path(crunchy_config_dict, crunchy_test_dir):
    """Test get_index_path"""

    # GIVEM a bam_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = crunchy_test_dir / "file.bam"

    # WHEN creating bam path
    bai_paths = crunchy_api.get_index_path(file_path=bam_path)

    # THEN this should replace current suffix with .bam.bai for double suffix
    # type and .bai for single suffix type
    assert bai_paths["double_suffix"].suffixes == [".bam", ".bai"]
    assert bai_paths["single_suffix"].suffixes == [".bai"]

    # GIVEN a bam_path
    cram_path = crunchy_test_dir / "file.cram"

    # WHEN creating flag path
    crai_paths = crunchy_api.get_index_path(file_path=cram_path)

    # THEN this should replace current suffix with .cram.crai for double suffix
    # type, and .crai for single suffix type
    assert crai_paths["double_suffix"].suffixes == [".cram", ".crai"]
    assert crai_paths["single_suffix"].suffixes == [".crai"]


def test_get_cram_path_from_bam(crunchy_config_dict, crunchy_test_dir):
    """Test change_suffic_bam_to_cram"""
    # GIVEN a bam_path
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    bam_path = crunchy_test_dir / "file.bam"

    # WHEN changing suffix to cram
    cram_path = crunchy_api.get_cram_path_from_bam(bam_path=bam_path)

    # THEN suffix should be .cram
    assert cram_path.suffix == CRAM_SUFFIX


def test_fastq_to_spring(
    crunchy_config_dict, sbatch_content_spring, fastq_paths, mocker
):
    """Test fastq_to_spring method"""
    # GIVEN a crunchy-api, and fastq paths
    mocker_submit_sbatch = mocker.patch.object(CrunchyAPI, "_submit_sbatch")
    crunchy_api = CrunchyAPI(crunchy_config_dict)

    # WHEN calling fastq_to_spring on fastq files
    fastq_first = fastq_paths["fastq_first_path"]
    fastq_second = fastq_paths["fastq_second_path"]
    crunchy_api.fastq_to_spring(
        fastq_first=fastq_first,
        fastq_second=fastq_second,
        dry_run=False,
        ntasks=1,
        mem=2,
    )

    # THEN _submit_sbatch method is called with expected sbatch-content
    mocker_submit_sbatch.assert_called_with(
        sbatch_content=sbatch_content_spring, dry_run=False
    )


def test_is_compression_done_no_spring(crunchy_config_dict, existing_fastq_paths):
    """test if compression is done when no spring file"""
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    fastq_first = existing_fastq_paths["fastq_first_path"]
    fastq_second = existing_fastq_paths["fastq_second_path"]
    # GIVEN no spring file exists
    spring_file = CrunchyAPI.get_spring_path_from_fastq(fastq=fastq_first)
    assert not spring_file.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_spring_compression_done(
        fastq_first=fastq_first, fastq_second=fastq_second
    )

    # THEN result should be false
    assert not result


def test_is_compression_done_no_flag_spring(
    crunchy_config_dict, compressed_fastqs_without_flag
):
    """test if spring compression is done when no flag"""
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    fastq_first = compressed_fastqs_without_flag["fastq_first_path"]
    fastq_second = compressed_fastqs_without_flag["fastq_second_path"]
    # GIVEN a existing spring file
    spring_file = CrunchyAPI.get_spring_path_from_fastq(fastq=fastq_first)
    assert spring_file.exists()
    # GIVEN a non existing flag file
    flag_file = CrunchyAPI.get_flag_path(file_path=spring_file)
    assert not flag_file.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_spring_compression_done(
        fastq_first=fastq_first, fastq_second=fastq_second
    )

    # THEN result should be false
    assert not result


def test_is_compression_done_spring(crunchy_config_dict, compressed_fastqs):
    """test if compression is done when spring file exists"""
    # GIVEN a crunchy-api, and fastq paths
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    fastq_first = compressed_fastqs["fastq_first_path"]
    fastq_second = compressed_fastqs["fastq_second_path"]
    # GIVEN a existing spring file
    spring_file = CrunchyAPI.get_spring_path_from_fastq(fastq=fastq_first)
    assert spring_file.exists()
    # GIVEN a existing flag file
    flag_file = CrunchyAPI.get_flag_path(file_path=spring_file)
    assert flag_file.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_spring_compression_done(
        fastq_first=fastq_first, fastq_second=fastq_second
    )

    # THEN result should be True
    assert result


def test_get_spring_path_from_fastq():
    """Test to get a spring path"""
    # GIVEN a fastq path for a read 1 in pair
    ind_id = "ind1"
    fastq = Path("".join([ind_id, FASTQ_FIRST_READ_SUFFIX]))

    # WHEN fetching the spring path
    spring_path = CrunchyAPI.get_spring_path_from_fastq(fastq)

    # THEN check that the correct path was returned
    assert spring_path == Path(ind_id).with_suffix(".spring")


def test_get_spring_path_from_second_fastq():
    """Test to get a spring path from second read in pair"""
    # GIVEN a fastq path for a read 2 in pair
    ind_id = "ind1"
    fastq = Path("".join([ind_id, FASTQ_SECOND_READ_SUFFIX]))

    # WHEN fetching the spring path
    spring_path = CrunchyAPI.get_spring_path_from_fastq(fastq)

    # THEN check that the correct path was returned
    assert spring_path == Path(ind_id).with_suffix(".spring")


def test_is_not_pending(crunchy_config_dict, fastq_paths):
    """test if spring compression is pending"""
    # GIVEN a crunchy-api, and a fastq file
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    fastq_first = fastq_paths["fastq_first_path"]
    # GIVEN a non existing pending flag
    pending_path = crunchy_api.get_pending_path(file_path=fastq_first)
    assert not pending_path.exists()

    # WHEN checking if spring compression is done
    result = crunchy_api.is_spring_compression_pending(fastq=fastq_first)

    # THEN result should be False since the pending flag is not there
    assert result is False


def test_is_pending(crunchy_config_dict, compressed_fastqs_pending):
    """test if spring compression is pending"""
    # GIVEN a crunchy-api, and fastq files
    crunchy_api = CrunchyAPI(crunchy_config_dict)
    fastq_first = compressed_fastqs_pending["fastq_first_path"]
    # GIVEN a existing pending flag
    pending_path = crunchy_api.get_pending_path(file_path=fastq_first)
    assert pending_path.exists()

    # WHEN checking if spring compression is pending
    result = crunchy_api.is_spring_compression_pending(fastq=fastq_first)

    # THEN result should be True since the pending_path exists
    assert result is True
