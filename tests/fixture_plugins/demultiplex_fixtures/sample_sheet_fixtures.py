from pathlib import Path

import pytest

from cg.apps.demultiplex.sample_sheet.sample_sheet_models import SampleSheet
from cg.apps.demultiplex.sample_sheet.sample_sheet_validator import SampleSheetValidator
from cg.constants.constants import FileFormat
from cg.constants.demultiplexing import BclConverter
from cg.io.controller import ReadFile


@pytest.fixture(scope="function")
def sample_sheet_validator() -> SampleSheetValidator:
    """Return a sample sheet validator."""
    return SampleSheetValidator()


@pytest.fixture
def hiseq_x_single_index_sample_sheet_content(
    hiseq_x_single_index_sample_sheet_path: Path,
) -> list[list[str]]:
    """Return the content of a single-index HiSeq X sample sheet."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=hiseq_x_single_index_sample_sheet_path
    )


@pytest.fixture
def hiseq_x_single_index_bcl2fastq_sample_sheet_content(
    hiseq_x_single_index_bcl2fastq_sample_sheet_path: Path,
) -> list[list[str]]:
    """Return the path to a single-index Bcl2fastq HiSeq X sample sheet."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=hiseq_x_single_index_bcl2fastq_sample_sheet_path
    )


@pytest.fixture
def hiseq_x_dual_index_sample_sheet_content(
    hiseq_x_dual_index_sample_sheet_path: Path,
) -> list[list[str]]:
    """Return the content of a dual-index HiSeq X sample sheet."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=hiseq_x_dual_index_sample_sheet_path
    )


@pytest.fixture
def hiseq_x_dual_index_bcl2fastq_sample_sheet_content(
    hiseq_x_dual_index_bcl2fastq_sample_sheet_path: Path,
) -> list[list[str]]:
    """Return the path to a dual-index Bcl2fastq HiSeq X sample sheet."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=hiseq_x_dual_index_bcl2fastq_sample_sheet_path
    )


@pytest.fixture
def hiseq_2500_dual_index_sample_sheet_content(
    hiseq_2500_dual_index_sample_sheet_path: Path,
) -> list[list[str]]:
    """Return the content of a dual-index HiSeq 2500 sample sheet."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=hiseq_2500_dual_index_sample_sheet_path
    )


@pytest.fixture
def hiseq_2500_dual_index_bcl2fastq_sample_sheet_content(
    hiseq_2500_dual_index_bcl2fastq_sample_sheet_path: Path,
) -> list[list[str]]:
    """Return the path to a dual-index Bcl2fastq HiSeq 2500 sample sheet."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=hiseq_2500_dual_index_bcl2fastq_sample_sheet_path
    )


@pytest.fixture
def hiseq_2500_custom_index_sample_sheet_content(
    hiseq_2500_custom_index_sample_sheet_path: Path,
) -> list[list[str]]:
    """Return the content of a custom-index HiSeq 2500 sample sheet."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=hiseq_2500_custom_index_sample_sheet_path
    )


@pytest.fixture
def hiseq_2500_custom_index_bcl2fastq_sample_sheet_content(
    hiseq_2500_custom_index_bcl2fastq_sample_sheet_path: Path,
) -> list[list[str]]:
    """Return the path to a custom-index Bcl2fastq HiSeq 2500 sample sheet."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=hiseq_2500_custom_index_bcl2fastq_sample_sheet_path
    )


@pytest.fixture
def novaseq_6000_pre_1_5_kits_sample_sheet_content(
    novaseq_6000_pre_1_5_kits_correct_sample_sheet_path: Path,
) -> list[list[str]]:
    """Return the content of a NovaSeq 6000 sample sheet."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=novaseq_6000_pre_1_5_kits_correct_sample_sheet_path
    )


@pytest.fixture
def novaseq_6000_post_1_5_kits_sample_sheet_content(
    novaseq_6000_post_1_5_kits_correct_sample_sheet_path: Path,
) -> list[list[str]]:
    """Return the content of a NovaSeq 6000 sample sheet."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=novaseq_6000_post_1_5_kits_correct_sample_sheet_path
    )


@pytest.fixture
def novaseq_x_sample_sheet_content(novaseq_x_correct_sample_sheet: Path) -> list[list[str]]:
    """Return the content of a NovaSeqX sample sheet."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=novaseq_x_correct_sample_sheet
    )


@pytest.fixture
def novaseq_6000_sample_sheet_with_reversed_cycles_content(
    novaseq_6000_sample_sheet_with_reversed_cycles: Path,
) -> list[list[str]]:
    """Return the content of a NovaSeq 6000 sample sheet with reversed cycles."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=novaseq_6000_sample_sheet_with_reversed_cycles
    )


@pytest.fixture
def novaseq_x_sample_sheet_with_forward_cycles_content(
    novaseq_x_sample_sheet_with_forward_cycles: Path,
) -> list[list[str]]:
    """Return the content of a NovaSeqX sample sheet with forward cycles."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=novaseq_x_sample_sheet_with_forward_cycles
    )


@pytest.fixture
def sample_sheet_content_missing_data_header() -> list[list[str]]:
    """Return a sample sheet content with only headers."""
    return [["[Header]"], ["[Reads]"], ["[BCLConvert_Settings]"]]


@pytest.fixture
def novaseq_6000_post_1_5_kits_sample_sheet_object(
    sample_sheet_validator: SampleSheetValidator,
    novaseq_6000_post_1_5_kits_correct_sample_sheet_path: Path,
) -> SampleSheet:
    """Return a NovaSeq 6000 sample sheet object."""
    return sample_sheet_validator.get_sample_sheet_object_from_file(
        file_path=novaseq_6000_post_1_5_kits_correct_sample_sheet_path,
        bcl_converter=BclConverter.BCLCONVERT,
    )
