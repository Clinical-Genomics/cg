"""Tests for CrunchyAPI"""

import logging
from pathlib import Path
from typing import Any

from cg.apps.crunchy import CrunchyAPI
from cg.apps.crunchy.files import get_tmp_dir, update_metadata_date
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile, WriteFile
from cg.models.compression_data import CompressionData


def test_get_tmp_path_correct_place(project_dir: Path):
    """Test to get the path to a temporary directory"""
    # GIVEN a crunchy API
    prefix = "spring_"
    suffix = "fastq_"

    # WHEN creating a tmpdir path
    tmp_dir = get_tmp_dir(prefix=prefix, suffix=suffix, base=str(project_dir))

    # THEN assert that the path is correct
    assert isinstance(tmp_dir, str)
    tmp_dir_path = Path(tmp_dir)
    # THEN assert the dir is in the correct place
    assert tmp_dir_path.parent == project_dir


def test_set_dry_run(crunchy_config: dict[str, dict[str, Any]]):
    """Test to set the dry run of the api"""
    # GIVEN a crunchy API where dry run is False
    crunchy_api = CrunchyAPI(crunchy_config)
    assert crunchy_api.dry_run is False

    # WHEN updating the dry run
    crunchy_api.set_dry_run(True)

    # THEN assert that the api has true dry run
    assert crunchy_api.dry_run is True


def test_is_fastq_compression_possible(compression_object: CompressionData, caplog):
    """Test if FASTQ compression is possible under correct circumstances

    This means that there should exist FASTQ files but no SPRING archive
    """
    caplog.set_level(logging.DEBUG)
    compression_object.fastq_first.touch()
    compression_object.fastq_second.touch()
    # GIVEN no SPRING file exists
    spring_file = compression_object.spring_path
    assert not spring_file.exists()

    # WHEN checking if SPRING compression is done
    result = compression_object.is_fastq_compression_possible

    # THEN result should be True
    assert result is True
    # THEN assert that the correct message was communicated
    assert "FASTQ compression is possible" in caplog.text


def test_is_fastq_compression_possible_compression_pending(
    compression_object: CompressionData, caplog
):
    """Test if FASTQ compression is possible when FASTQ compression is pending

    This means that there should exist a FASTQ compression flag
    """
    caplog.set_level(logging.DEBUG)
    compression_object.fastq_first.touch()
    compression_object.fastq_second.touch()
    # GIVEN that the pending path exists
    compression_object.pending_path.touch()
    # GIVEN no SPRING file exists
    spring_file = compression_object.spring_path
    assert not spring_file.exists()

    # WHEN checking if SPRING compression is done
    result = compression_object.is_fastq_compression_possible

    # THEN result should be False since the compression flag exists
    assert not result
    # THEN assert that the correct message was communicated
    assert "Compression/decompression is pending for" in caplog.text


def test_is_fastq_compression_possible_spring_exists(compression_object: CompressionData, caplog):
    """Test if FASTQ compression is possible when FASTQ compression is done

    This means that the SPRING file exists
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN that the SPRING path exists
    compression_object.spring_path.touch()
    spring_file = compression_object.spring_path
    assert spring_file.exists()

    # WHEN checking if SPRING compression is done
    result = compression_object.is_fastq_compression_possible

    # THEN result should be False since the compression flag exists
    assert result is False
    # THEN assert that the correct message was communicated
    assert "SPRING file found" in caplog.text


def test_is_compression_done(
    real_crunchy_api,
    spring_metadata_file: Path,
    compression_object: CompressionData,
    caplog,
):
    """Test if compression is done when everything is correct"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and FASTQ paths
    # GIVEN no SPRING file exists
    compression_object.spring_path.touch()
    assert spring_metadata_file == compression_object.spring_metadata_path
    assert spring_metadata_file.exists()

    # WHEN checking if SPRING compression is done
    result = compression_object.is_fastq_compression_done

    # THEN result should be True
    assert result is True
    # THEN assert that the correct message was communicated
    assert "FASTQ compression is done" in caplog.text


def test_is_compression_done_no_spring(
    real_crunchy_api: CrunchyAPI, compression_object: CompressionData, caplog
):
    """Test if compression is done when no SPRING archive"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and FASTQ paths
    # GIVEN no SPRING file exists
    spring_file = compression_object.spring_path
    assert not spring_file.exists()

    # WHEN checking if SPRING compression is done
    result = compression_object.is_fastq_compression_done

    # THEN result should be false
    assert not result
    # THEN assert that the correct message was communicated
    assert f"No SPRING file for {compression_object.run_name}" in caplog.text


def test_is_compression_done_no_flag_spring(
    real_crunchy_api: CrunchyAPI, compression_object: CompressionData, caplog
):
    """Test if SPRING compression is done when no metadata file"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and FASTQ paths
    # GIVEN a existing SPRING file
    compression_object.spring_path.touch()
    assert compression_object.spring_path.exists()
    # GIVEN a non-existing flag file
    assert not compression_object.spring_metadata_path.exists()

    # WHEN checking if SPRING compression is done
    result = compression_object.is_fastq_compression_done

    # THEN result should be false
    assert not result
    # THEN assert that the correct message was communicated
    assert "No metadata file found" in caplog.text


def test_is_compression_done_spring(
    real_crunchy_api: CrunchyAPI,
    compression_object: CompressionData,
    spring_metadata_file: Path,
    caplog,
):
    """Test if compression is done when SPRING files exists"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and FASTQ paths
    # GIVEN a existing SPRING file
    compression_object.spring_path.touch()
    assert compression_object.spring_path.exists()
    # GIVEN a existing flag file
    assert spring_metadata_file == compression_object.spring_metadata_path
    assert compression_object.spring_metadata_path.exists()

    # WHEN checking if SPRING compression is done
    result = compression_object.is_fastq_compression_done

    # THEN result should be True
    assert result
    # THEN assert that the correct message was communicated
    assert f"FASTQ compression is done for {compression_object.run_name}" in caplog.text


def test_is_compression_done_spring_new_files(
    real_crunchy_api: CrunchyAPI,
    compression_object: CompressionData,
    spring_metadata_file: Path,
    caplog,
):
    """Test if compression is done when FASTQ files have been unpacked

    This test should fail since the FASTQ files are new
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and FASTQ paths
    # GIVEN a existing SPRING file
    compression_object.spring_path.touch()
    assert compression_object.spring_path.exists()
    # GIVEN a existing flag file
    metadata_file = compression_object.spring_metadata_path
    assert spring_metadata_file == compression_object.spring_metadata_path
    assert metadata_file.exists()

    # GIVEN that the files where updated less than three weeks ago
    update_metadata_date(metadata_file)
    content: list[dict[str, str]] = ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=metadata_file
    )
    for file_info in content:
        assert "updated" in file_info

    # WHEN checking if SPRING compression is done
    result = compression_object.is_fastq_compression_done

    # THEN result should be False since the updated date < 3 weeks
    assert result is False
    # THEN assert that correct information is logged
    assert "FASTQ files are not old enough" in caplog.text


def test_is_compression_done_spring_old_files(
    real_crunchy_api: CrunchyAPI,
    compression_object: CompressionData,
    spring_metadata_file: Path,
    caplog,
):
    """Test if compression is done when FASTQ files are updated a long time ago

    The function should return True since files are old
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and FASTQ paths
    # GIVEN a existing SPRING file
    compression_object.spring_path.touch()
    assert compression_object.spring_path.exists()
    # GIVEN a existing flag file
    metadata_file = compression_object.spring_metadata_path
    assert spring_metadata_file == compression_object.spring_metadata_path
    assert metadata_file.exists()

    # GIVEN that the files where updated less than three weeks ago
    update_metadata_date(metadata_file)
    content = ReadFile.get_content_from_file(file_format=FileFormat.JSON, file_path=metadata_file)
    for file_info in content:
        file_info["updated"] = "2019-01-01"

    WriteFile.write_file_from_content(
        content=content, file_format=FileFormat.JSON, file_path=metadata_file
    )

    # WHEN checking if SPRING compression is done
    result = compression_object.is_fastq_compression_done

    # THEN result should be True since the updated date > 3 weeks
    assert result is True
    # THEN assert that correct information is logged
    assert "FASTQ compression is done" in caplog.text


def test_is_spring_decompression_possible_no_fastq(compression_object: CompressionData, caplog):
    """Test if decompression is possible when there are no FASTQ files

    The function should return true since there are no FASTQ files
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api
    # GIVEN a existing SPRING file
    compression_object.spring_path.touch()
    assert compression_object.spring_path.exists()
    # GIVEN that there are no fastq files
    compression_object.fastq_first.unlink()
    compression_object.fastq_second.unlink()
    assert not compression_object.fastq_first.exists()
    assert not compression_object.fastq_second.exists()

    # WHEN checking if SPRING compression is done
    result: bool = compression_object.is_spring_decompression_possible

    # THEN result should be True since there are no fastq files
    assert result is True
    # THEN assert the correct information is communicated
    assert "Decompression is possible" in caplog.text


def test_is_spring_decompression_possible_no_spring(compression_object: CompressionData, caplog):
    """Test if decompression is possible when there are no SPRING archive

    The function should return False since there is no SPRING archive
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and FASTQ paths

    # WHEN checking if SPRING compression is done
    result: bool = compression_object.is_spring_decompression_possible

    # THEN result should be False since there is no SPRING archive
    assert result is False
    # THEN assert the correct information is communicated
    assert "No SPRING file found" in caplog.text


def test_is_spring_decompression_possible_fastq(compression_object: CompressionData, caplog):
    """Test if decompression is possible when there are existing FASTQ files

    The function should return False since there are decompressed FASTQ files
    """
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and FASTQ paths
    # GIVEN a existing SPRING file
    compression_object.spring_path.touch()
    # GIVEN that the FASTQ files exists
    compression_object.fastq_first.touch()
    compression_object.fastq_second.touch()

    # WHEN checking if SPRING decompression is possible
    result: bool = compression_object.is_spring_decompression_possible

    # THEN result should be False since the FASTQ files already exists
    assert result is False
    # THEN assert the correct information is communicated
    assert "FASTQ files already exists" in caplog.text


def test_is_not_pending_when_no_flag_file(
    real_crunchy_api: CrunchyAPI, compression_object: CompressionData
):
    """Test if SPRING compression is pending when no flag file"""
    # GIVEN a crunchy-api, and a FASTQ file
    # GIVEN a non-existing pending flag
    assert not compression_object.pending_path.exists()

    # WHEN checking if SPRING compression is ongoing
    result: bool = compression_object.is_compression_pending

    # THEN result should be False since the pending flag is not there
    assert result is False


def test_is_pending(real_crunchy_api: CrunchyAPI, compression_object: CompressionData):
    """Test if SPRING compression is pending when pending file exists"""
    # GIVEN a crunchy-api, and FASTQ files
    # GIVEN a existing pending flag
    compression_object.pending_path.touch()
    assert compression_object.pending_path.exists()

    # WHEN checking if SPRING compression is pending
    result: bool = compression_object.is_compression_pending

    # THEN result should be True since the pending_path exists
    assert result is True
