"""Utility functions for the downsampledata module."""
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.store import Store
from cg.store.models import Family, Sample
from cg.utils.files import get_files_matching_pattern


def case_exists_in_statusdb(status_db: Store, case_name: str) -> bool:
    """Check if a case exists in StatusDB."""
    case: Family = status_db.get_case_by_name(case_name)
    if case:
        return True
    return False


def sample_exists_in_statusdb(status_db: Store, sample_id: str) -> bool:
    """Check if a sample exists in StatusDB."""
    sample: Sample = status_db.get_sample_by_internal_id(sample_id)
    if sample:
        return True
    return False


def add_downsampled_sample_to_housekeeper(
    fastq_file_output_directory: str, sample_id: str, housekeeper_api: HousekeeperAPI
) -> None:
    """Add a downsampled sample to housekeeper and include the fastq files."""
    create_downsampled_sample_bundle(sample_id=sample_id, housekeeper_api=housekeeper_api)
    add_downsampled_fastq_files_to_housekeeper(
        sample_id=sample_id,
        housekeeper_api=housekeeper_api,
        fastq_file_output_directory=fastq_file_output_directory,
    )


def add_downsampled_fastq_files_to_housekeeper(
    fastq_file_output_directory: str, sample_id: str, housekeeper_api: HousekeeperAPI
) -> None:
    """Add down sampled fastq files to housekeeper."""
    fastq_file_paths: list[Path] = get_files_matching_pattern(
        directory=Path(fastq_file_output_directory),
        pattern=f"*{sample_id}*.{SequencingFileTag.FASTQ}.gz",
    )
    for fastq_file_path in fastq_file_paths:
        housekeeper_api.add_and_include_file_to_latest_version(
            bundle_name=sample_id,
            file=fastq_file_path,
            tags=[SequencingFileTag.FASTQ],
        )


def create_downsampled_sample_bundle(housekeeper_api: HousekeeperAPI, sample_id: str) -> None:
    """Create a new bundle for the downsampled sample in housekeeper."""
    housekeeper_api.create_new_bundle_and_version(name=sample_id)
