from pathlib import Path

import pytest

from cg.apps.demultiplex.sample_sheet.sample_sheet_validator import SampleSheetValidator


@pytest.fixture
def hiseq_x_single_index_sample_sheet_validator(
    hiseq_x_single_index_sample_sheet_path: Path,
) -> SampleSheetValidator:
    """Return a HiseqX single index sample sheet validator."""
    return SampleSheetValidator(path=hiseq_x_single_index_sample_sheet_path)


@pytest.fixture
def hiseq_x_single_index_bcl2fastq_sample_sheet_validator(
    hiseq_x_single_index_bcl2fastq_sample_sheet: Path,
) -> SampleSheetValidator:
    """Return a HiseqX dual index sample sheet validator."""
    return SampleSheetValidator(path=hiseq_x_single_index_bcl2fastq_sample_sheet)


@pytest.fixture
def hiseq_x_dual_index_sample_sheet_validator(
    hiseq_x_dual_index_sample_sheet_path: Path,
) -> SampleSheetValidator:
    """Return a HiseqX dual index sample sheet validator."""
    return SampleSheetValidator(path=hiseq_x_dual_index_sample_sheet_path)


@pytest.fixture
def hiseq_x_dual_index_bcl2fastq_sample_sheet_validator(
    hiseq_x_dual_index_bcl2fastq_sample_sheet: Path,
) -> SampleSheetValidator:
    """Return a HiseqX dual index  Bcl2fastq sample sheet validator."""
    return SampleSheetValidator(path=hiseq_x_dual_index_bcl2fastq_sample_sheet)


@pytest.fixture
def hiseq_2500_dual_index_sample_sheet_validator(
    hiseq_2500_dual_index_sample_sheet_path: Path,
) -> SampleSheetValidator:
    """Return a Hiseq 2500 dual index sample sheet validator."""
    return SampleSheetValidator(path=hiseq_2500_dual_index_sample_sheet_path)


@pytest.fixture
def hiseq_2500_dual_index_bcl2fastq_sample_sheet_validator(
    hiseq_2500_dual_index_bcl2fastq_sample_sheet: Path,
) -> SampleSheetValidator:
    """Return a Hiseq 2500 dual index sample sheet validator."""
    return SampleSheetValidator(path=hiseq_2500_dual_index_bcl2fastq_sample_sheet)


@pytest.fixture
def hiseq_2500_custom_index_sample_sheet_validator(
    hiseq_2500_custom_index_sample_sheet_path: Path,
) -> SampleSheetValidator:
    """Return a Hiseq 2500 custom index sample sheet validator."""
    return SampleSheetValidator(path=hiseq_2500_custom_index_sample_sheet_path)


@pytest.fixture
def hiseq_2500_custom_index_bcl2fastq_sample_sheet_validator(
    hiseq_2500_custom_index_bcl2fastq_sample_sheet: Path,
) -> SampleSheetValidator:
    """Return a Hiseq 2500 custom index sample sheet validator."""
    return SampleSheetValidator(path=hiseq_2500_custom_index_bcl2fastq_sample_sheet)


@pytest.fixture
def novaseq_6000_pre_1_5_kits_sample_sheet_validator(
    novaseq_6000_pre_1_5_kits_correct_sample_sheet_path: Path,
) -> SampleSheetValidator:
    """Return a NovaSeq 6000 pre 1.5 kits sample sheet validator."""
    return SampleSheetValidator(path=novaseq_6000_pre_1_5_kits_correct_sample_sheet_path)


@pytest.fixture
def novaseq_6000_post_1_5_kits_sample_sheet_validator(
    novaseq_6000_post_1_5_kits_correct_sample_sheet_path: Path,
) -> SampleSheetValidator:
    """Return a NovaSeq 6000 post 1.5 kits sample sheet validator."""
    return SampleSheetValidator(path=novaseq_6000_post_1_5_kits_correct_sample_sheet_path)


@pytest.fixture
def novaseq_x_sample_sheet_validator(
    novaseq_x_correct_sample_sheet: Path,
) -> SampleSheetValidator:
    """Return a NovaSeq X sample sheet validator."""
    return SampleSheetValidator(path=novaseq_x_correct_sample_sheet)
