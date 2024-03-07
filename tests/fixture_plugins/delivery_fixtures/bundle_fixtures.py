"""Delivery API bundle fixtures."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from cg.constants import SequencingFileTag
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG, AlignmentFileTag


@pytest.fixture
def hk_delivery_sample_bundle(
    sample_hk_bundle_no_files: dict[str, Any],
    sample_id: str,
    fastq_sample_file: Path,
    spring_sample_file: Path,
) -> dict:
    sample_hk_bundle: dict[str, Any] = deepcopy(sample_hk_bundle_no_files)
    sample_hk_bundle["name"] = sample_id
    sample_hk_bundle["files"] = [
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
    return sample_hk_bundle


@pytest.fixture
def hk_delivery_another_sample_bundle(
    sample_hk_bundle_no_files: dict[str, Any],
    another_sample_id: str,
    fastq_another_sample_file: Path,
    spring_another_sample_file: Path,
) -> dict:
    sample_hk_bundle: dict[str, Any] = deepcopy(sample_hk_bundle_no_files)
    sample_hk_bundle["name"] = another_sample_id
    sample_hk_bundle["files"] = [
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
    return sample_hk_bundle


@pytest.fixture
def hk_delivery_case_bundle(
    case_hk_bundle_no_files: dict[str, Any],
    case_id: str,
    sample_id: str,
    another_sample_id: str,
    case_report_file: Path,
    sample_cram_file: Path,
    another_sample_cram_file: Path,
) -> dict:
    case_hk_bundle: dict[str, Any] = deepcopy(case_hk_bundle_no_files)
    case_hk_bundle["name"] = case_id
    case_hk_bundle["files"] = [
        {
            "archive": False,
            "path": case_report_file.as_posix(),
            "tags": [HK_DELIVERY_REPORT_TAG, case_id],
        },
        {
            "archive": False,
            "path": sample_cram_file.as_posix(),
            "tags": [AlignmentFileTag.CRAM, sample_id],
        },
        {
            "archive": False,
            "path": another_sample_cram_file.as_posix(),
            "tags": [AlignmentFileTag.CRAM, another_sample_id],
        },
    ]
    return case_hk_bundle
