"""Fixtures for parsed raw LIMS samples for demultiplexing and sample sheet creation."""

from pathlib import Path

import pytest

from cg.apps.demultiplex.sample_sheet.sample_models import (
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import (
    SampleSheetCreatorBCLConvert,
)
from cg.constants import FileExtensions
from cg.io.json import read_json
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData


@pytest.fixture
def hiseq_x_single_index_bcl_convert_lims_samples(
    hiseq_x_single_index_flow_cell_dir: Path,
) -> list[FlowCellSampleBCLConvert]:
    """Return a list of BCLConvert samples parsed from LIMS for a HiSeqX single index flow cell."""
    path = Path(
        hiseq_x_single_index_flow_cell_dir, f"HJCFFALXX_bcl_convert_raw{FileExtensions.JSON}"
    )
    return [FlowCellSampleBCLConvert.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def hiseq_x_dual_index_bcl_convert_lims_samples(
    hiseq_x_dual_index_flow_cell_dir: Path,
) -> list[FlowCellSampleBCLConvert]:
    """Return a list of BCLConvert samples parsed from LIMS for a HiSeqX dual index flow cell."""
    path = Path(hiseq_x_dual_index_flow_cell_dir, f"HL32LCCXY_bcl_convert_raw{FileExtensions.JSON}")
    return [FlowCellSampleBCLConvert.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def hiseq_2500_dual_index_bcl_convert_lims_samples(
    hiseq_2500_dual_index_flow_cell_dir: Path,
) -> list[FlowCellSampleBCLConvert]:
    """Return a list of BCLConvert samples parsed from LIMS for a HiSeq2500 dual index flow cell."""
    path = Path(hiseq_2500_dual_index_flow_cell_dir, "HM2LNBCX2_bcl_convert_raw.json")
    return [FlowCellSampleBCLConvert.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def hiseq_2500_custom_index_bcl_convert_lims_samples(
    hiseq_2500_custom_index_flow_cell_dir: Path,
) -> list[FlowCellSampleBCLConvert]:
    """Return a list of BCLConvert samples parsed from LIMS for a HiSeq2500 custom index flow cell."""
    path = Path(hiseq_2500_custom_index_flow_cell_dir, "HGYFNBCX2_bcl_convert_raw.json")
    return [FlowCellSampleBCLConvert.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def novaseq_6000_pre_1_5_kits_bcl2fastq_lims_samples(
    novaseq_6000_pre_1_5_kits_flow_cell_path: Path,
) -> list[FlowCellSampleBcl2Fastq]:
    """Return a list of Bcl2Fastq samples parsed from LIMS for a NovaSeq6000 pre 1.5 flow cell."""
    path = Path(novaseq_6000_pre_1_5_kits_flow_cell_path, "HLYWYDSXX_bcl2fastq_raw.json")
    return [FlowCellSampleBcl2Fastq.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def novaseq_6000_pre_1_5_kits_bcl_convert_lims_samples(
    novaseq_6000_pre_1_5_kits_flow_cell_path: Path,
) -> list[FlowCellSampleBCLConvert]:
    """Return a list of BCLConvert samples parsed from LIMS for a NovaSeq6000 pre 1.5 flow cell."""
    path = Path(novaseq_6000_pre_1_5_kits_flow_cell_path, "HLYWYDSXX_bcl_convert_raw.json")
    return [FlowCellSampleBCLConvert.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def novaseq_6000_post_1_5_kits_bcl_convert_lims_samples(
    novaseq_6000_post_1_5_kits_flow_cell_path: Path,
) -> list[FlowCellSampleBCLConvert]:
    """Return a list of BCLConvert samples parsed from LIMS for a NovaSeq6000 post 1.5 flow cell."""
    path = Path(novaseq_6000_post_1_5_kits_flow_cell_path, "HK33MDRX3_bcl_convert_raw.json")
    return [FlowCellSampleBCLConvert.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def novaseq_x_lims_samples(novaseq_x_flow_cell_directory: Path) -> list[FlowCellSampleBCLConvert]:
    """Return a list of BCLConvert samples parsed from LIMS for a NovaSeqX flow cell."""
    path = Path(novaseq_x_flow_cell_directory, "22F52TLT3_raw.json")
    return [FlowCellSampleBCLConvert.model_validate(sample) for sample in read_json(path)]


# Sample sheet creators


@pytest.fixture
def bcl_convert_sample_sheet_creator(
    novaseq_x_flow_cell: FlowCellDirectoryData,
    novaseq_x_lims_samples: list[FlowCellSampleBCLConvert],
) -> SampleSheetCreatorBCLConvert:
    """Returns a sample sheet creator for sample sheet v2."""
    return SampleSheetCreatorBCLConvert(
        flow_cell=novaseq_x_flow_cell,
        lims_samples=novaseq_x_lims_samples,
    )
