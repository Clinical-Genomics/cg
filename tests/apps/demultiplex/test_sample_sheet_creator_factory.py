"""Tests for the creation of the sample sheet"""

from cg.apps.demultiplex.sample_sheet.create import get_sample_sheet_creator
from cg.apps.demultiplex.sample_sheet.sample_models import (
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import (
    SampleSheetCreator,
    SampleSheetCreatorBcl2Fastq,
    SampleSheetCreatorBCLConvert,
)
from cg.constants.demultiplexing import BclConverter
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData


def test_sample_sheet_creator_factory_novaseq_6000(
    novaseq_6000_pre_1_5_kits_flow_cell_bcl2fastq: FlowCellDirectoryData,
    novaseq_6000_pre_1_5_kits_bcl2fastq_lims_samples: list[FlowCellSampleBcl2Fastq],
):
    """Test that a sample sheet creator defined with NovaSeq6000 data is V1."""
    # GIVEN a NovaSeq6000 flow cell and a list of NovaSeq6000 samples

    # GIVEN that the flow cell is demultiplexed with bcl2fastq
    assert novaseq_6000_pre_1_5_kits_flow_cell_bcl2fastq.bcl_converter == BclConverter.BCL2FASTQ

    # WHEN defining the sample sheet creator
    sample_sheet_creator: SampleSheetCreator = get_sample_sheet_creator(
        flow_cell=novaseq_6000_pre_1_5_kits_flow_cell_bcl2fastq,
        lims_samples=novaseq_6000_pre_1_5_kits_bcl2fastq_lims_samples,
        force=False,
    )

    # THEN no error is raised and the sample sheet creator is a Bcl2Fastq sample sheet creator
    assert isinstance(sample_sheet_creator, SampleSheetCreatorBcl2Fastq)


def test_sample_sheet_creator_factory_bcl_convert(
    novaseq_x_flow_cell: FlowCellDirectoryData,
    novaseq_x_lims_samples: list[FlowCellSampleBCLConvert],
):
    """Test that a sample sheet creator defined with BCL convert data is BCL Convert."""

    # GIVEN a NovaSeqX flow cell and a list of NovaSeqX BCL Convert samples
    assert novaseq_x_flow_cell.bcl_converter == BclConverter.BCLCONVERT

    # WHEN defining the sample sheet creator
    sample_sheet_creator: SampleSheetCreator = get_sample_sheet_creator(
        flow_cell=novaseq_x_flow_cell,
        lims_samples=novaseq_x_lims_samples,
        force=False,
    )

    # THEN the sample sheet creator is a BCL Convert sample sheet creator
    assert isinstance(sample_sheet_creator, SampleSheetCreatorBCLConvert)
