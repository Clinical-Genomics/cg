"""Test methods for compressing FASTQ"""
import logging
from pathlib import Path
from typing import Dict, List

import pytest
from cg.apps.crunchy import CrunchyAPI
from cg.apps.crunchy.files import (
    get_crunchy_metadata,
    get_fastq_to_spring_sbatch_path,
    get_log_dir,
    get_spring_archive_files,
)
from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants.constants import FileFormat
from cg.io.controller import WriteFile
from cg.models import CompressionData
from cg.utils import Process
from cgmodels.crunchy.metadata import CrunchyFile, CrunchyMetadata
from pydantic import ValidationError


def test_get_spring_metadata(spring_metadata_file: Path):
    """Test the method that fetches the SPRING metadata from a file"""
    # GIVEN a SPRING path and the path to a populated SPRING metadata file
    assert spring_metadata_file.is_file()
    assert spring_metadata_file.exists()

    # WHEN fetching the content of the file
    parsed_content: CrunchyMetadata = get_crunchy_metadata(spring_metadata_file)

    # THEN assert information about the three files is there
    assert len(parsed_content.files) == 3
    # THEN assert a list with the files is returned
    assert isinstance(parsed_content.files, list)


def test_get_spring_archive_files(crunchy_metadata_object: CrunchyMetadata):
    """Test the method that sorts the SPRING metadata into a dictionary"""
    # GIVEN a SPRING metadata content in its raw format
    assert isinstance(crunchy_metadata_object.files, list)

    # WHEN sorting the files
    sorted_content: Dict[str, CrunchyFile] = get_spring_archive_files(crunchy_metadata_object)

    # THEN assert information about the three files is there
    assert len(sorted_content) == 3
    # THEN assert a dictionary with the files is returned
    assert isinstance(sorted_content, dict)
    # THEN assert that the correct files are there
    for file_name in ["fastq_first", "fastq_second", "spring"]:
        assert file_name in sorted_content


def test_get_spring_metadata_malformed_info(
    spring_metadata_file: Path, spring_metadata: List[dict]
):
    """Test the method that fetches the SPRING metadata from a file when file is malformed"""
    # GIVEN a SPRING metadata file with missing information
    spring_metadata[0].pop("path")
    WriteFile.write_file_from_content(
        content=spring_metadata, file_format=FileFormat.JSON, file_path=spring_metadata_file
    )

    # WHEN fetching the content of the file
    with pytest.raises(ValidationError):
        # THEN assert that a pydantic validation error is raised
        get_crunchy_metadata(spring_metadata_file)


def test_get_spring_metadata_wrong_number_files(
    spring_metadata_file: Path, spring_metadata: List[dict]
):
    """Test the method that fetches the SPRING metadata from a file when a file is missing"""
    # GIVEN a SPRING metadata file with missing file
    spring_metadata = spring_metadata[1:]
    WriteFile.write_file_from_content(
        content=spring_metadata, file_format=FileFormat.JSON, file_path=spring_metadata_file
    )

    # WHEN fetching the content of the file
    with pytest.raises(ValidationError):
        # THEN assert that a validation error is raised
        get_crunchy_metadata(spring_metadata_file)


def test_fastq_to_spring_sbatch(
    crunchy_config: dict,
    compression_object: CompressionData,
    sbatch_process: Process,
    sbatch_job_number: int,
    caplog,
):
    """Test fastq_to_spring method"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and FASTQ paths

    crunchy_api = CrunchyAPI(crunchy_config)
    crunchy_api.slurm_api.process = sbatch_process
    spring_path: Path = compression_object.spring_path
    log_path: Path = get_log_dir(spring_path)
    run_name: str = compression_object.run_name
    sbatch_path: Path = get_fastq_to_spring_sbatch_path(log_dir=log_path, run_name=run_name)

    # GIVEN that the sbatch file does not exist
    assert not sbatch_path.is_file()
    # GIVEN that the pending path does not exist
    assert compression_object.pending_exists() is False

    # WHEN calling fastq_to_spring on FASTQ files
    job_number: int = crunchy_api.fastq_to_spring(compression_obj=compression_object)

    # THEN assert that the sbatch file was created
    assert sbatch_path.is_file()
    # THEN assert that correct job number was returned
    assert job_number == sbatch_job_number
    # THEN assert that the pending path was created
    assert compression_object.pending_exists() is True


def test_spring_to_fastq(
    compression_object: CompressionData,
    spring_metadata_file: Path,
    crunchy_config: dict,
    mocker,
):
    """Test SPRING to FASTQ method

    Test to decompress SPRING to FASTQ. This test will make sure that the correct sbatch content
    was submitted to the Process api
    """
    # GIVEN a crunchy-api given an existing SPRING metadata file
    assert spring_metadata_file.exists()
    mocker_submit_sbatch = mocker.patch.object(SlurmAPI, "submit_sbatch")
    crunchy_api = CrunchyAPI(crunchy_config)
    # GIVEN that the pending path does not exist
    assert compression_object.pending_exists() is False

    # WHEN calling bam_to_cram method on bam-path
    crunchy_api.spring_to_fastq(compression_obj=compression_object)

    # THEN _submit_sbatch method is called
    mocker_submit_sbatch.assert_called()
    # THEN assert that the pending path was created
    assert compression_object.pending_exists() is True
