"""Utility functions for the downsampledata module."""

import logging
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.utils.files import get_files_matching_pattern

LOG = logging.getLogger(__name__)


def store_downsampled_sample_bundle(
    fastq_file_output_directory: str, sample_id: str, housekeeper_api: HousekeeperAPI
) -> None:
    """
    Add a downsampled sample bundle to housekeeper and include the fastq files.
    Raises:
        FileExistsError
    """
    if not Path(fastq_file_output_directory).exists():
        raise FileExistsError(f"Cannot find: {fastq_file_output_directory}")
    create_downsampled_sample_bundle(sample_id=sample_id, housekeeper_api=housekeeper_api)
    store_downsampled_fastq_files_from_dir(
        sample_id=sample_id,
        housekeeper_api=housekeeper_api,
        fastq_file_output_directory=fastq_file_output_directory,
    )


def store_downsampled_fastq_files_from_dir(
    fastq_file_output_directory: str, sample_id: str, housekeeper_api: HousekeeperAPI
) -> None:
    """
    Add downsampled fastq files from the given directory to housekeeper.
    Raises:
        FileNotFoundError
    """
    fastq_file_paths: list[Path] = get_files_matching_pattern(
        directory=Path(fastq_file_output_directory),
        pattern=f"*{sample_id.split(sep='DS')[0]}*.{SequencingFileTag.FASTQ}.gz",
    )
    if not fastq_file_paths:
        raise FileNotFoundError(
            f"No fastq files found with pattern: *{sample_id}*.{SequencingFileTag.FASTQ}.gz"
        )
    for fastq_file_path in fastq_file_paths:
        LOG.debug(f"Found file: {fastq_file_path}")
        housekeeper_api.add_and_include_file_to_latest_version(
            bundle_name=sample_id,
            file=fastq_file_path,
            tags=[SequencingFileTag.FASTQ, sample_id],
        )


def create_downsampled_sample_bundle(housekeeper_api: HousekeeperAPI, sample_id: str) -> None:
    """Create a new bundle for the downsampled sample in housekeeper."""
    housekeeper_api.create_new_bundle_and_version(name=sample_id)
