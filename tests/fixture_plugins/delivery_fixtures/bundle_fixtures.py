"""Delivery API bundle fixtures."""

from pathlib import Path

import pytest

from cg.constants import SequencingFileTag


@pytest.fixture
def hk_delivery_sample_bundle(
    sample_hk_bundle_no_files: dict,
    sample_id: str,
    spring_sample_file: Path,
    fastq_sample_file: Path,
) -> dict:
    """Return Housekeeper bundle for another sample."""
    sample_hk_bundle_no_files["name"] = sample_id
    sample_hk_bundle_no_files["files"] = [
        {
            "archive": False,
            "path": fastq_sample_file.as_posix(),
            "tags": [SequencingFileTag.FASTQ, sample_id],
        },
        {
            "archive": False,
            "path": spring_sample_file.as_posix(),
            "tags": [SequencingFileTag.SPRING, sample_id],
        },
    ]
    return sample_hk_bundle_no_files


@pytest.fixture
def hk_delivery_another_sample_bundle(
    sample_hk_bundle_no_files: dict,
    another_sample_id: str,
    spring_another_sample_file: Path,
    fastq_another_sample_file: Path,
) -> dict:
    """Return Housekeeper bundle for another sample."""
    sample_hk_bundle_no_files["name"] = another_sample_id
    sample_hk_bundle_no_files["files"] = [
        {
            "archive": False,
            "path": fastq_another_sample_file.as_posix(),
            "tags": [SequencingFileTag.FASTQ, another_sample_id],
        },
        {
            "archive": False,
            "path": spring_another_sample_file.as_posix(),
            "tags": [SequencingFileTag.SPRING, another_sample_id],
        },
    ]
    return sample_hk_bundle_no_files
