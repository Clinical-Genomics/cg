"""Delivery API bundle fixtures."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from cg.constants import SequencingFileTag
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG, AlignmentFileTag


@pytest.fixture
def hk_delivery_fastq_sample_bundle(
    sample_hk_bundle_no_files: dict[str, Any],
    sample_id: str,
    delivery_fastq_file: Path,
    delivery_spring_file: Path,
) -> dict:
    sample_hk_bundle: dict[str, Any] = deepcopy(sample_hk_bundle_no_files)
    sample_hk_bundle["name"] = sample_id
    sample_hk_bundle["files"] = [
        {
            "archive": False,
            "path": delivery_fastq_file.as_posix(),
            "tags": [SequencingFileTag.FASTQ, sample_id],
        },
        {
            "archive": False,
            "path": delivery_spring_file.as_posix(),
            "tags": [SequencingFileTag.SPRING, sample_id],
        },
    ]
    return sample_hk_bundle


@pytest.fixture
def hk_delivery_another_fastq_sample_bundle(
    sample_hk_bundle_no_files: dict[str, Any],
    another_sample_id: str,
    delivery_fastq_file: Path,
    delivery_spring_file: Path,
) -> dict:
    sample_hk_bundle: dict[str, Any] = deepcopy(sample_hk_bundle_no_files)
    sample_hk_bundle["name"] = another_sample_id
    sample_hk_bundle["files"] = [
        {
            "archive": False,
            "path": delivery_fastq_file.as_posix(),
            "tags": [SequencingFileTag.FASTQ, another_sample_id],
        },
        {
            "archive": False,
            "path": delivery_spring_file.as_posix(),
            "tags": [SequencingFileTag.SPRING, another_sample_id],
        },
    ]
    return sample_hk_bundle


@pytest.fixture
def hk_delivery_bam_sample_bundle(
    sample_hk_bundle_no_files: dict[str, Any],
    sample_id: str,
    delivery_bam_file: Path,
) -> dict:
    sample_hk_bundle: dict[str, Any] = deepcopy(sample_hk_bundle_no_files)
    sample_hk_bundle["name"] = sample_id
    sample_hk_bundle["files"] = [
        {
            "archive": False,
            "path": delivery_bam_file.as_posix(),
            "tags": [AlignmentFileTag.BAM, sample_id],
        },
    ]
    return sample_hk_bundle


@pytest.fixture
def hk_delivery_another_bam_sample_bundle(
    sample_hk_bundle_no_files: dict[str, Any],
    another_sample_id: str,
    delivery_bam_file: Path,
) -> dict:
    sample_hk_bundle: dict[str, Any] = deepcopy(sample_hk_bundle_no_files)
    sample_hk_bundle["name"] = another_sample_id
    sample_hk_bundle["files"] = [
        {
            "archive": False,
            "path": delivery_bam_file.as_posix(),
            "tags": [AlignmentFileTag.BAM, another_sample_id],
        },
    ]
    return sample_hk_bundle


@pytest.fixture
def hk_delivery_case_bundle(
    case_hk_bundle_no_files: dict[str, Any],
    case_id: str,
    sample_id: str,
    another_sample_id: str,
    delivery_report_file: Path,
    delivery_cram_file: Path,
    delivery_another_cram_file: Path,
) -> dict:
    case_hk_bundle: dict[str, Any] = deepcopy(case_hk_bundle_no_files)
    case_hk_bundle["name"] = case_id
    case_hk_bundle["files"] = [
        {
            "archive": False,
            "path": delivery_report_file.as_posix(),
            "tags": [HK_DELIVERY_REPORT_TAG, case_id],
        },
        {
            "archive": False,
            "path": delivery_cram_file.as_posix(),
            "tags": [AlignmentFileTag.CRAM, sample_id],
        },
        {
            "archive": False,
            "path": delivery_another_cram_file.as_posix(),
            "tags": [AlignmentFileTag.CRAM, another_sample_id],
        },
    ]
    return case_hk_bundle


@pytest.fixture
def hk_delivery_case_bundle_fohm_upload(
    case_hk_bundle_no_files: dict[str, Any],
    case_id: str,
    sample_id: str,
    another_sample_id: str,
    delivery_report_file: Path,
    delivery_case_fastq_file: Path,
    delivery_another_case_fastq_file: Path,
    delivery_consensus_sample_file: Path,
    delivery_another_consensus_sample_file: Path,
    delivery_vcf_report_file: Path,
    delivery_another_vcf_report_file: Path,
) -> dict:
    case_hk_bundle: dict[str, Any] = deepcopy(case_hk_bundle_no_files)
    case_hk_bundle["name"] = case_id
    case_hk_bundle["files"] = [
        {
            "archive": False,
            "path": delivery_report_file.as_posix(),
            "tags": [HK_DELIVERY_REPORT_TAG, case_id],
        },
        {
            "archive": False,
            "path": delivery_case_fastq_file.as_posix(),
            "tags": ["fastq", sample_id],
        },
        {
            "archive": False,
            "path": delivery_another_case_fastq_file.as_posix(),
            "tags": ["fastq", another_sample_id],
        },
        {
            "archive": False,
            "path": delivery_consensus_sample_file.as_posix(),
            "tags": ["consensus-sample", sample_id],
        },
        {
            "archive": False,
            "path": delivery_another_consensus_sample_file.as_posix(),
            "tags": ["consensus-sample", another_sample_id],
        },
        {
            "archive": False,
            "path": delivery_vcf_report_file.as_posix(),
            "tags": ["vcf-report", sample_id],
        },
        {
            "archive": False,
            "path": delivery_another_vcf_report_file.as_posix(),
            "tags": ["vcf-report", another_sample_id],
        },
    ]
    return case_hk_bundle
