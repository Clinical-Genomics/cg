"""Tests for the creation of the sample sheet"""
from typing import List
from cg.apps.demultiplex.sample_sheet.create import get_sample_sheet_creator
from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import (
    SampleSheetCreator,
    SampleSheetCreatorV1,
    SampleSheetCreatorV2,
)
from cg.apps.demultiplex.sample_sheet.models import (
    FlowCellSampleNovaSeqX,
    FlowCellSampleNovaSeq6000Bcl2Fastq,
)
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData


def test_sample_sheet_creator_factory_novaseq_6000(
    bcl2fastq_flow_cell: FlowCellDirectoryData,
    lims_novaseq_bcl2fastq_samples: List[FlowCellSampleNovaSeq6000Bcl2Fastq],
):
    """Test that a sample sheet creator defined with NovaSeq6000 data is V1."""
    # GIVEN a NovaSeq6000 flow cell and a list of NovaSeq6000 samples

    # WHEN defining the sample sheet creator
    sample_sheet_creator: SampleSheetCreator = get_sample_sheet_creator(
        bcl_converter=bcl2fastq_flow_cell.bcl_converter,
        flow_cell=bcl2fastq_flow_cell,
        lims_samples=lims_novaseq_bcl2fastq_samples,
        force=False,
    )

    # THEN no error is raised and the sample sheet creator is v1
    assert isinstance(sample_sheet_creator, SampleSheetCreatorV1)


def test_sample_sheet_creator_factory_novaseq_x(
    novaseq_x_flow_cell: FlowCellDirectoryData,
    lims_novaseq_x_samples: List[FlowCellSampleNovaSeqX],
):
    """Test that a sample sheet creator defined with NovaSeq6000 data is V1."""
    # GIVEN a NovaSeqX flow cell and a list of NovaSeqX samples

    # WHEN defining the sample sheet creator
    sample_sheet_creator: SampleSheetCreator = get_sample_sheet_creator(
        bcl_converter=novaseq_x_flow_cell.bcl_converter,
        flow_cell=novaseq_x_flow_cell,
        lims_samples=lims_novaseq_x_samples,
        force=False,
    )

    # THEN no error is raised and the sample sheet creator is v1
    assert isinstance(sample_sheet_creator, SampleSheetCreatorV2)
