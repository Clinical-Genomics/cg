"""Tests for the SampleSheetCreator classes."""
import pytest

from pathlib import Path
from typing import List
from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import (
    SampleSheetCreator,
    SampleSheetCreatorV1,
    SampleSheetCreatorV2,
)
from cg.apps.demultiplex.sample_sheet.models import (
    SampleSheet,
    FlowCellSampleNovaSeq6000Bcl2Fastq,
    FlowCellSampleNovaSeq6000Dragen,
    FlowCellSampleNovaSeqX,
)
from cg.apps.demultiplex.sample_sheet.read_sample_sheet import get_validated_sample_sheet
from cg.constants.demultiplexing import BclConverter
from cg.exc import SampleSheetError
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData


def test_v2_sample_sheet_fails_with_bcl2fastq(
    novaseq_x_flow_cell: FlowCellDirectoryData, lims_novaseq_x_samples: List[FlowCellSampleNovaSeqX]
):
    """Test that creating a v2 sample sheet fails if the bcl converter is Bcl2fastq."""
    # GIVEN a NovaSeqX flow cell and samples

    # WHEN trying to instantiate a SampleSheetCreatorV2 with bcl2fastq as bcl_converter
    with pytest.raises(SampleSheetError) as exc_info:
        SampleSheetCreatorV2(
            flow_cell=novaseq_x_flow_cell,
            lims_samples=lims_novaseq_x_samples,
            bcl_converter=BclConverter.BCL2FASTQ,
        )
        # THEN an error is raised
        assert str(exc_info.value) == f"Can't use {BclConverter.BCL2FASTQ} with sample sheet v2"


def test_add_dummy_samples_for_sample_sheet_v1(
    novaseq6000_flow_cell_sample_1: FlowCellSampleNovaSeq6000Bcl2Fastq,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
):
    """Test that dummy samples are added when needed for a NovaSeq6000 sample sheet."""
    # GIVEN a list of one NovaSeq6000 sample and a sample sheet creator with the sample
    samples: List[FlowCellSampleNovaSeq6000Bcl2Fastq] = [novaseq6000_flow_cell_sample_1]
    assert len(samples) == 1
    sample_sheet_creator = SampleSheetCreatorV1(
        flow_cell=bcl2fastq_flow_cell, lims_samples=samples, bcl_converter=BclConverter.BCL2FASTQ
    )

    # WHEN adding dummy samples
    sample_sheet_creator.add_dummy_samples()

    # THEN the list of sample has increased in size
    assert len(sample_sheet_creator.lims_samples) > 1


def test_construct_bcl2fastq_sheet(
    novaseq_bcl2fastq_sample_sheet_creator: SampleSheetCreator, project_dir: Path
):
    """Test that a created Bcl2fastq sample sheet has samples."""
    # GIVEN a V1 sample sheet creator populated with Bcl2fastq samples
    assert novaseq_bcl2fastq_sample_sheet_creator.lims_samples

    # WHEN building the sample sheet
    sample_sheet_content: List[
        List[str]
    ] = novaseq_bcl2fastq_sample_sheet_creator.construct_sample_sheet()

    # THEN a correctly formatted sample sheet was created
    sample_sheet: SampleSheet = get_validated_sample_sheet(
        sample_sheet_content=sample_sheet_content,
        sample_type=FlowCellSampleNovaSeq6000Bcl2Fastq,
    )
    assert sample_sheet.samples


def test_construct_dragen_sheet(
    novaseq_dragen_sample_sheet_creator: SampleSheetCreator, project_dir: Path
):
    """Test that a created Dragen sample sheet has samples."""
    # GIVEN a V1 sample sheet creator populated with Dragen samples
    assert novaseq_dragen_sample_sheet_creator.lims_samples

    # WHEN building the sample sheet
    sample_sheet_content: List[
        List[str]
    ] = novaseq_dragen_sample_sheet_creator.construct_sample_sheet()

    # THEN a correctly formatted sample sheet was created
    sample_sheet: SampleSheet = get_validated_sample_sheet(
        sample_sheet_content=sample_sheet_content,
        sample_type=FlowCellSampleNovaSeq6000Dragen,
    )
    assert sample_sheet.samples


def test_construct_novaseq_x_sheet(
    novaseq_x_sample_sheet_creator: SampleSheetCreator, project_dir: Path
):
    """Test that a created NovaSeqX sample sheet has samples."""
    # GIVEN a V2 sample sheet creator populated with Dragen samples
    assert novaseq_x_sample_sheet_creator.lims_samples

    # WHEN building the sample sheet
    sample_sheet_content: List[List[str]] = novaseq_x_sample_sheet_creator.construct_sample_sheet()

    # THEN a correctly formatted sample sheet was created
    sample_sheet: SampleSheet = get_validated_sample_sheet(
        sample_sheet_content=sample_sheet_content,
        sample_type=FlowCellSampleNovaSeqX,
    )
    assert sample_sheet.samples


def test_remove_unwanted_samples_dual_index(
    novaseq6000_flow_cell_sample_before_adapt_indexes: FlowCellSampleNovaSeq6000Bcl2Fastq,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
):
    """Test that a sample with dual index is not removed."""
    # GIVEN a sample sheet creator with a sample with dual index
    sample_sheet_creator: SampleSheetCreatorV1 = SampleSheetCreatorV1(
        flow_cell=bcl2fastq_flow_cell,
        lims_samples=[novaseq6000_flow_cell_sample_before_adapt_indexes],
        bcl_converter=BclConverter.BCL2FASTQ,
    )

    # WHEN removing unwanted samples
    sample_sheet_creator.remove_unwanted_samples()

    # THEN the sample is not removed
    assert len(sample_sheet_creator.lims_samples) == 1


def test_remove_unwanted_samples_no_dual_index(
    novaseq6000_flow_cell_sample_no_dual_index: FlowCellSampleNovaSeq6000Bcl2Fastq,
    bcl2fastq_flow_cell: FlowCellDirectoryData,
    caplog,
):
    """Test that samples with no dual index are removed."""
    # GIVEN a sample sheet creator with a sample without dual indexes
    sample_sheet_creator: SampleSheetCreatorV1 = SampleSheetCreatorV1(
        flow_cell=bcl2fastq_flow_cell,
        lims_samples=[novaseq6000_flow_cell_sample_no_dual_index],
        bcl_converter=BclConverter.BCL2FASTQ,
    )

    # WHEN removing unwanted samples
    sample_sheet_creator.remove_unwanted_samples()

    # THEN the only sample is removed
    assert len(sample_sheet_creator.lims_samples) == 0
    assert (
        f"Removing sample {novaseq6000_flow_cell_sample_no_dual_index} since it does not have dual index"
        in caplog.text
    )
