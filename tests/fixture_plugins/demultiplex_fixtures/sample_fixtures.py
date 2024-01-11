"""Demultiplex sample fixtures."""
from pathlib import Path

import pytest

from cg.apps.demultiplex.sample_sheet.sample_models import (
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import SampleSheetCreatorBCLConvert
from cg.constants import FileExtensions
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.io.json import read_json
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData


@pytest.fixture
def lims_novaseq_bcl_convert_samples(
    lims_novaseq_samples_raw: list[dict],
) -> list[FlowCellSampleBCLConvert]:
    """Return a list of parsed flow cell samples demultiplexed with BCL convert."""
    return [FlowCellSampleBCLConvert.model_validate(sample) for sample in lims_novaseq_samples_raw]


@pytest.fixture
def lims_novaseq_bcl2fastq_samples(
    lims_novaseq_samples_raw: list[dict],
) -> list[FlowCellSampleBcl2Fastq]:
    """Return a list of parsed Bcl2fastq flow cell samples"""
    return [FlowCellSampleBcl2Fastq.model_validate(sample) for sample in lims_novaseq_samples_raw]


@pytest.fixture
def lims_novaseq_6000_bcl2fastq_samples(
    lims_novaseq_6000_sample_raw: list[dict],
) -> list[FlowCellSampleBcl2Fastq]:
    """Return a list of parsed Bcl2fastq flow cell samples"""
    return [
        FlowCellSampleBcl2Fastq.model_validate(sample) for sample in lims_novaseq_6000_sample_raw
    ]


@pytest.fixture
def bcl_convert_sample_sheet_creator(
    bcl_convert_flow_cell: FlowCellDirectoryData,
    lims_novaseq_bcl_convert_samples: list[FlowCellSampleBCLConvert],
) -> SampleSheetCreatorBCLConvert:
    """Returns a sample sheet creator for version 2 sample sheets with dragen format."""
    return SampleSheetCreatorBCLConvert(
        flow_cell=bcl_convert_flow_cell,
        lims_samples=lims_novaseq_bcl_convert_samples,
    )


@pytest.fixture
def novaseq_6000_post_1_5_kits_lims_samples(
    novaseq_6000_post_1_5_kits_raw_lims_samples: Path,
) -> list[FlowCellSampleBCLConvert]:
    return [
        FlowCellSampleBCLConvert.model_validate(sample)
        for sample in read_json(novaseq_6000_post_1_5_kits_raw_lims_samples)
    ]


@pytest.fixture
def novaseq_6000_pre_1_5_kits_lims_samples(
    novaseq_6000_pre_1_5_kits_raw_lims_samples: Path,
) -> list[FlowCellSampleBCLConvert]:
    return [
        FlowCellSampleBCLConvert.model_validate(sample)
        for sample in read_json(novaseq_6000_pre_1_5_kits_raw_lims_samples)
    ]


@pytest.fixture
def novaseq_x_lims_samples(novaseq_x_raw_lims_samples: Path) -> list[FlowCellSampleBCLConvert]:
    return [
        FlowCellSampleBCLConvert.model_validate(sample)
        for sample in read_json(novaseq_x_raw_lims_samples)
    ]


@pytest.fixture
def hiseq_x_single_index_bcl_convert_lims_samples(
    hiseq_x_single_index_flow_cell_dir: Path,
) -> list[FlowCellSampleBCLConvert]:
    """Return a list of BCLConvert samples from a HiSeqX single index flow cell."""
    path = Path(
        hiseq_x_single_index_flow_cell_dir, f"HJCFFALXX_bcl_convert_raw{FileExtensions.JSON}"
    )
    return [FlowCellSampleBCLConvert.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def hiseq_x_dual_index_bcl_convert_lims_samples(
    hiseq_x_dual_index_flow_cell_dir: Path,
) -> list[FlowCellSampleBCLConvert]:
    """Return a list of BCLConvert samples from a HiSeqX dual index flow cell."""
    path = Path(hiseq_x_dual_index_flow_cell_dir, f"HL32LCCXY_bcl_convert_raw{FileExtensions.JSON}")
    return [FlowCellSampleBCLConvert.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def hiseq_2500_dual_index_bcl_convert_lims_samples(
    hiseq_2500_dual_index_flow_cell_dir: Path,
) -> list[FlowCellSampleBCLConvert]:
    """Return a list of BCLConvert samples from a HiSeq2500 dual index flow cell."""
    path = Path(hiseq_2500_dual_index_flow_cell_dir, "HM2LNBCX2_bcl_convert_raw.json")
    return [FlowCellSampleBCLConvert.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def hiseq_2500_custom_index_bcl_convert_lims_samples(
    hiseq_2500_custom_index_flow_cell_dir: Path,
) -> list[FlowCellSampleBCLConvert]:
    """Return a list of BCLConvert samples from a HiSeq2500 custom index flow cell."""
    path = Path(hiseq_2500_custom_index_flow_cell_dir, "HGYFNBCX2_bcl_convert_raw.json")
    return [FlowCellSampleBCLConvert.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def lims_novaseq_samples_raw(lims_novaseq_samples_file: Path) -> list[dict]:
    """Return a list of raw flow cell samples."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=lims_novaseq_samples_file
    )


@pytest.fixture
def lims_novaseq_6000_sample_raw(lims_novaseq_6000_samples_file: Path) -> list[dict]:
    """Return the list of raw samples from flow cell HVKJCDRXX."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=lims_novaseq_6000_samples_file
    )
