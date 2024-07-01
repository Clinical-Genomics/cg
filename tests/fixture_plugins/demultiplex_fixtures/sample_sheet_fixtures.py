from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from cg.apps.demultiplex.sample_sheet.sample_models import FlowCellSample
from cg.apps.demultiplex.sample_sheet.sample_sheet_models import SampleSheet
from cg.apps.demultiplex.sample_sheet.sample_sheet_validator import SampleSheetValidator
from cg.constants.constants import FileFormat
from cg.constants.demultiplexing import SampleSheetBcl2FastqSections, SampleSheetBCLConvertSections
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
def hiseq_x_dual_index_sample_sheet_content(
    hiseq_x_dual_index_sample_sheet_path: Path,
) -> list[list[str]]:
    """Return the content of a dual-index HiSeq X sample sheet."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=hiseq_x_dual_index_sample_sheet_path
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
def hiseq_2500_custom_index_sample_sheet_content(
    hiseq_2500_custom_index_sample_sheet_path: Path,
) -> list[list[str]]:
    """Return the content of a custom-index HiSeq 2500 sample sheet."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=hiseq_2500_custom_index_sample_sheet_path
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
def novaseq_6000_post_1_5_kits_sample_sheet_with_selected_samples(
    novaseq_6000_post_1_5_kits_bcl_convert_lims_samples: list[FlowCellSample],
    selected_novaseq_6000_post_1_5_kits_sample_ids: list[str],
) -> SampleSheet:
    """Return a NovaSeq 6000 sample sheet with selected samples."""
    selected_samples: list[FlowCellSample] = []
    for sample in novaseq_6000_post_1_5_kits_bcl_convert_lims_samples:
        if sample.sample_id in selected_novaseq_6000_post_1_5_kits_sample_ids:
            selected_samples.append(sample)
    return SampleSheet(samples=selected_samples)


@pytest.fixture
def novaseq_x_sample_sheet_content(novaseq_x_correct_sample_sheet: Path) -> list[list[str]]:
    """Return the content of a NovaSeqX sample sheet."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=novaseq_x_correct_sample_sheet
    )


# Sample sheet parts


@pytest.fixture
def bcl_convert_sample_sheet_line_entry_1() -> list[str]:
    """Return a sample sheet line entry from the HiSeqX double index flow cell."""
    return [
        "1",
        "ACC4519A1",
        "ATTCAGAA",
        "TATAGCCT",
        "Y151;I8;I8;Y151",
        "1",
        "1",
    ]


@pytest.fixture
def bcl_convert_sample_sheet_line_entry_2() -> list[str]:
    """Return a sample sheet line entry from the HiSeqX double index flow cell."""
    return [
        "2",
        "ACC4519A2",
        "GAATTCGT",
        "TATAGCCT",
        "Y151;I8;I8;Y151",
        "1",
        "1",
    ]


@pytest.fixture
def sample_sheet_bcl2fastq_data_header() -> list[list[str]]:
    """Return the content of a Bcl2fastq sample sheet data header without samples."""
    return [
        [SampleSheetBcl2FastqSections.Data.HEADER],
        [
            SampleSheetBcl2FastqSections.Data.FLOW_CELL_ID.value,
            SampleSheetBcl2FastqSections.Data.LANE.value,
            SampleSheetBcl2FastqSections.Data.SAMPLE_INTERNAL_ID_BCL2FASTQ.value,
            SampleSheetBcl2FastqSections.Data.SAMPLE_REFERENCE.value,
            SampleSheetBcl2FastqSections.Data.INDEX_1.value,
            SampleSheetBcl2FastqSections.Data.INDEX_2.value,
            SampleSheetBcl2FastqSections.Data.SAMPLE_NAME.value,
            SampleSheetBcl2FastqSections.Data.CONTROL.value,
            SampleSheetBcl2FastqSections.Data.RECIPE.value,
            SampleSheetBcl2FastqSections.Data.OPERATOR.value,
            SampleSheetBcl2FastqSections.Data.SAMPLE_PROJECT_BCL2FASTQ.value,
        ],
    ]


@pytest.fixture
def sample_sheet_bcl_convert_data_header() -> list[list[str]]:
    """Return the content of a BCLConvert sample sheet data header without samples."""
    return [
        [SampleSheetBCLConvertSections.Data.HEADER],
        [
            SampleSheetBCLConvertSections.Data.LANE.value,
            SampleSheetBCLConvertSections.Data.SAMPLE_INTERNAL_ID.value,
            SampleSheetBCLConvertSections.Data.INDEX_1.value,
            SampleSheetBCLConvertSections.Data.INDEX_2.value,
            SampleSheetBCLConvertSections.Data.OVERRIDE_CYCLES.value,
            SampleSheetBCLConvertSections.Data.BARCODE_MISMATCHES_1.value,
            SampleSheetBCLConvertSections.Data.BARCODE_MISMATCHES_2.value,
        ],
    ]


@pytest.fixture
def sample_sheet_bcl2fastq_data_header_with_replaced_sample_id() -> list[list[str]]:
    """Return the content of a Bcl2fastq sample sheet data header without samples."""
    return [
        [SampleSheetBcl2FastqSections.Data.HEADER],
        [
            SampleSheetBcl2FastqSections.Data.FLOW_CELL_ID.value,
            SampleSheetBcl2FastqSections.Data.LANE.value,
            SampleSheetBCLConvertSections.Data.SAMPLE_INTERNAL_ID.value,
            SampleSheetBcl2FastqSections.Data.SAMPLE_REFERENCE.value,
            SampleSheetBcl2FastqSections.Data.INDEX_1.value,
            SampleSheetBcl2FastqSections.Data.INDEX_2.value,
            SampleSheetBcl2FastqSections.Data.SAMPLE_NAME.value,
            SampleSheetBcl2FastqSections.Data.CONTROL.value,
            SampleSheetBcl2FastqSections.Data.RECIPE.value,
            SampleSheetBcl2FastqSections.Data.OPERATOR.value,
            SampleSheetBcl2FastqSections.Data.SAMPLE_PROJECT_BCL2FASTQ.value,
        ],
    ]


# Incorrect sample sheets


@pytest.fixture
def sample_sheet_content_missing_data_header() -> list[list[str]]:
    """Return a sample sheet without data and without the data header."""
    return [["[Header]"], ["[Reads]"], ["[BCLConvert_Settings]"]]


@pytest.fixture
def sample_sheet_samples_no_column_names(
    bcl_convert_sample_sheet_line_entry_1: list[str],
    bcl_convert_sample_sheet_line_entry_2: list[str],
) -> list[list[str]]:
    """Return the content of a sample sheet with samples but without the column names."""
    return [
        [SampleSheetBCLConvertSections.Data.HEADER],
        bcl_convert_sample_sheet_line_entry_1,
        bcl_convert_sample_sheet_line_entry_2,
    ]


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


# Sample sheet objects


@pytest.fixture
def novaseq_6000_post_1_5_kits_sample_sheet_object(
    sample_sheet_validator: SampleSheetValidator,
    novaseq_6000_post_1_5_kits_correct_sample_sheet_path: Path,
) -> SampleSheet:
    """Return a NovaSeq 6000 sample sheet object."""
    return sample_sheet_validator.get_sample_sheet_object_from_file(
        file_path=novaseq_6000_post_1_5_kits_correct_sample_sheet_path
    )


# HK bundle objects


@pytest.fixture
def sample_sheet_bcl2fastq_bundle_data(
    tmp_flow_cell_with_bcl2fastq_sample_sheet: Path,
    timestamp_yesterday: datetime,
) -> dict[str, Any]:
    """Return a sample sheet bundle data dictionary."""
    flow_cell_id: str = tmp_flow_cell_with_bcl2fastq_sample_sheet.name[-9:]
    return {
        "name": flow_cell_id,
        "created": timestamp_yesterday,
        "expires": timestamp_yesterday,
        "files": [
            {
                "path": Path(
                    tmp_flow_cell_with_bcl2fastq_sample_sheet, "SampleSheet.csv"
                ).as_posix(),
                "archive": False,
                "tags": ["samplesheet", flow_cell_id],
            },
        ],
    }
