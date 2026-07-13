"""Test methods for compressing FASTQ"""

import logging
from pathlib import Path
from unittest import mock

import pytest
from pydantic import ValidationError

from cg.apps.crunchy import CrunchyAPI
from cg.apps.crunchy.files import (
    get_crunchy_metadata,
    get_fastq_to_spring_sbatch_path,
    get_log_dir,
    get_spring_archive_files,
)
from cg.apps.crunchy.models import CrunchyFile, CrunchyMetadata
from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants.constants import FileFormat
from cg.io.controller import WriteFile
from cg.models.compression_data import CompressionData
from cg.utils import Process


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
    sorted_content: dict[str, CrunchyFile] = get_spring_archive_files(crunchy_metadata_object)

    # THEN assert information about the three files is there
    assert len(sorted_content) == 3
    # THEN assert a dictionary with the files is returned
    assert isinstance(sorted_content, dict)
    # THEN assert that the correct files are there
    for file_name in ["fastq_first", "fastq_second", "spring"]:
        assert file_name in sorted_content


def test_get_spring_metadata_malformed_info(
    spring_metadata_file: Path, spring_metadata: list[dict]
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
    spring_metadata_file: Path, spring_metadata: list[dict]
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
    job_number: int = crunchy_api.fastq_to_spring(
        compression_obj=compression_object,
        memory=crunchy_api.fallback_memory,
        minutes=crunchy_api.fallback_minutes,
    )

    # THEN assert that the sbatch file was created
    assert sbatch_path.is_file()
    # THEN assert that correct job number was returned
    assert job_number == sbatch_job_number
    # THEN assert that the pending path was created
    assert compression_object.pending_exists() is True

    # THEN assert the sbatch script requests the configured partition and chdir into tmp_dir_base
    sbatch_content: str = sbatch_path.read_text()
    assert f"#SBATCH --partition={crunchy_api.slurm_partition}" in sbatch_content
    assert f"#SBATCH --chdir={crunchy_api.tmp_dir_base}" in sbatch_content
    # THEN assert the scratch dir is node-local and keyed by the SLURM job id, unresolved
    assert f"{crunchy_api.tmp_dir_base}/${{SLURM_JOB_ID}}_spring" in sbatch_content
    # THEN assert the sbatch script requests the configured cpus-per-task
    assert f"#SBATCH --cpus-per-task={crunchy_api.slurm_cpus_per_task}" in sbatch_content


def test_fastq_to_spring_sbatch_without_cpus_per_task(
    crunchy_config: dict,
    compression_object: CompressionData,
    sbatch_process: Process,
):
    """Test that no --cpus-per-task header is added when it is not configured."""
    # GIVEN a crunchy-api with no cpus_per_task configured
    crunchy_config["crunchy"]["slurm"].pop("cpus_per_task")
    crunchy_api = CrunchyAPI(crunchy_config)
    crunchy_api.slurm_api.process = sbatch_process
    assert crunchy_api.slurm_cpus_per_task is None

    # WHEN calling fastq_to_spring on FASTQ files
    crunchy_api.fastq_to_spring(
        compression_obj=compression_object,
        memory=crunchy_api.fallback_memory,
        minutes=crunchy_api.fallback_minutes,
    )

    # THEN the sbatch script has no --cpus-per-task header
    sbatch_path: Path = get_fastq_to_spring_sbatch_path(
        log_dir=get_log_dir(compression_object.spring_path), run_name=compression_object.run_name
    )
    sbatch_content: str = sbatch_path.read_text()
    assert "--cpus-per-task" not in sbatch_content


def test_fastq_to_spring_sbatch_uses_explicit_memory_and_minutes(
    crunchy_config: dict,
    compression_object: CompressionData,
    sbatch_process: Process,
):
    """Test that memory/minutes passed to fastq_to_spring override the fallback defaults.

    These are per-job parameters, not stored on the CrunchyAPI instance, since a single
    CrunchyAPI is reused across every file being compressed.
    """
    # GIVEN a crunchy-api with configured fallback memory/minutes
    crunchy_api = CrunchyAPI(crunchy_config)
    crunchy_api.slurm_api.process = sbatch_process
    assert crunchy_api.fallback_memory != 77
    assert crunchy_api.fallback_minutes != 135

    # WHEN calling fastq_to_spring with explicit memory/minutes for this job
    crunchy_api.fastq_to_spring(compression_obj=compression_object, memory=77, minutes=135)

    # THEN the sbatch script reflects the explicit values (135 minutes = 2h15m), not the fallback
    sbatch_path: Path = get_fastq_to_spring_sbatch_path(
        log_dir=get_log_dir(compression_object.spring_path), run_name=compression_object.run_name
    )
    sbatch_content: str = sbatch_path.read_text()
    assert "#SBATCH --mem=77G" in sbatch_content
    assert "#SBATCH --time=2:15:00" in sbatch_content

    # THEN the CrunchyAPI instance's own config values are left untouched
    assert crunchy_api.fallback_memory != 77
    assert crunchy_api.fallback_minutes != 135


def test_spring_to_fastq(
    compression_object: CompressionData,
    spring_metadata_file: Path,
    crunchy_config: dict,
):
    """Test SPRING to FASTQ method

    Test to decompress SPRING to FASTQ. This test will make sure that the correct sbatch content
    was submitted to the Process api
    """
    # GIVEN a crunchy-api given an existing SPRING metadata file
    assert spring_metadata_file.exists()

    crunchy_api = CrunchyAPI(crunchy_config)
    # GIVEN that the pending path does not exist
    assert not compression_object.pending_exists()

    with mock.patch.object(SlurmAPI, "submit_sbatch", return_value=123456) as submit_sbatch:
        # WHEN calling bam_to_cram method on bam-path
        crunchy_api.spring_to_fastq(
            compression_obj=compression_object,
            memory=crunchy_api.fallback_memory,
            minutes=crunchy_api.fallback_minutes,
        )

        # THEN _submit_sbatch method is and the qos is high
        sbatch_content: str = submit_sbatch.call_args[1]["sbatch_content"]
        assert "--qos=high" in sbatch_content
        # THEN assert the sbatch script requests the configured partition and chdir
        assert f"#SBATCH --partition={crunchy_api.slurm_partition}" in sbatch_content
        assert f"#SBATCH --chdir={crunchy_api.tmp_dir_base}" in sbatch_content
        # THEN assert the scratch dir is node-local and keyed by the SLURM job id, unresolved
        assert f"{crunchy_api.tmp_dir_base}/${{SLURM_JOB_ID}}_spring" in sbatch_content
        # THEN assert the sbatch script requests the configured cpus-per-task
        assert f"#SBATCH --cpus-per-task={crunchy_api.slurm_cpus_per_task}" in sbatch_content

    # THEN assert that the pending path was created
    assert compression_object.pending_exists()


def test_spring_to_fastq_uses_explicit_memory_and_minutes(
    compression_object: CompressionData,
    spring_metadata_file: Path,
    crunchy_config: dict,
):
    """Test that memory/minutes passed to spring_to_fastq override the fallback defaults."""
    # GIVEN a crunchy-api with configured fallback memory/minutes
    assert spring_metadata_file.exists()
    crunchy_api = CrunchyAPI(crunchy_config)
    assert crunchy_api.fallback_memory != 42
    assert crunchy_api.fallback_minutes != 195

    with mock.patch.object(SlurmAPI, "submit_sbatch", return_value=123456) as submit_sbatch:
        # WHEN calling spring_to_fastq with explicit memory/minutes for this job
        crunchy_api.spring_to_fastq(compression_obj=compression_object, memory=42, minutes=195)

        # THEN the sbatch script reflects the explicit values (195 minutes = 3h15m)
        sbatch_content: str = submit_sbatch.call_args[1]["sbatch_content"]
        assert "#SBATCH --mem=42G" in sbatch_content
        assert "#SBATCH --time=3:15:00" in sbatch_content

    # THEN the CrunchyAPI instance's own config values are left untouched
    assert crunchy_api.fallback_memory != 42
    assert crunchy_api.fallback_minutes != 195
