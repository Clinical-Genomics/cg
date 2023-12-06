"""Tests for the SampleSheetCreator classes."""
from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest

from cg.apps.demultiplex.sample_sheet.models import (
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
    SampleSheet,
)
from cg.apps.demultiplex.sample_sheet.read_sample_sheet import (
    get_validated_sample_sheet,
)
from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import (
    SampleSheetCreator,
    SampleSheetCreatorBcl2Fastq,
    SampleSheetCreatorBCLConvert,
)
from cg.constants.demultiplexing import (
    NO_REVERSE_COMPLEMENTS,
    NOVASEQ_6000_POST_1_5_KITS,
    NOVASEQ_X_INDEX_SETTINGS,
    BclConverter,
    IndexSettings,
)
from cg.exc import SampleSheetError
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData


def test_bcl_convert_sample_sheet_fails_with_bcl2fastq(
    novaseq_x_flow_cell: FlowCellDirectoryData,
    lims_novaseq_bcl_convert_samples: list[FlowCellSampleBCLConvert],
):
    """Test that creating a BCL Convert sample sheet fails if the bcl converter is Bcl2fastq."""
    # GIVEN a NovaSeqX flow cell and samples and the bcl converter is Bcl2fastq
    novaseq_x_flow_cell.bcl_converter = BclConverter.BCL2FASTQ

    # WHEN trying to instantiate a SampleSheetCreatorBCLConvert with Bcl2fastq as bcl_converter
    with pytest.raises(SampleSheetError) as exc_info:
        SampleSheetCreatorBCLConvert(
            flow_cell=novaseq_x_flow_cell,
            lims_samples=lims_novaseq_bcl_convert_samples,
        )
        # THEN an error is raised
        assert (
            str(exc_info.value)
            == f"Can't use {BclConverter.BCL2FASTQ} with BCL Convert sample sheet"
        )


def test_construct_bcl2fastq_sheet(
    bcl2fastq_sample_sheet_creator: SampleSheetCreatorBcl2Fastq, project_dir: Path
):
    """Test that a created Bcl2fastq sample sheet has samples."""
    # GIVEN a Bcl2fastq sample sheet creator populated with Bcl2fastq samples
    assert bcl2fastq_sample_sheet_creator.lims_samples

    # WHEN building the sample sheet
    sample_sheet_content: list[list[str]] = bcl2fastq_sample_sheet_creator.construct_sample_sheet()

    # THEN a correctly formatted sample sheet was created
    sample_sheet: SampleSheet = get_validated_sample_sheet(
        sample_sheet_content=sample_sheet_content,
        sample_type=FlowCellSampleBcl2Fastq,
    )
    assert sample_sheet.samples


def test_construct_bcl_convert_sheet(
    bcl_convert_sample_sheet_creator: SampleSheetCreator, project_dir: Path
):
    """Test that a created BCL Convert sample sheet has samples."""
    # GIVEN a BCL convert sample sheet creator populated with BCL convert samples
    assert bcl_convert_sample_sheet_creator.lims_samples

    # WHEN building the sample sheet
    sample_sheet_content: list[
        list[str]
    ] = bcl_convert_sample_sheet_creator.construct_sample_sheet()

    # THEN a correctly formatted sample sheet was created
    sample_sheet: SampleSheet = get_validated_sample_sheet(
        sample_sheet_content=sample_sheet_content,
        sample_type=FlowCellSampleBCLConvert,
    )
    assert sample_sheet.samples


def test_remove_unwanted_samples_dual_index(
    novaseq6000_flow_cell_sample_before_adapt_indexes: FlowCellSampleBcl2Fastq,
    hiseq_x_flow_cell: FlowCellDirectoryData,
):
    """Test that a sample with dual index is not removed."""
    # GIVEN a sample sheet creator with a sample with dual index
    sample_sheet_creator: SampleSheetCreatorBcl2Fastq = SampleSheetCreatorBcl2Fastq(
        flow_cell=hiseq_x_flow_cell,
        lims_samples=[novaseq6000_flow_cell_sample_before_adapt_indexes],
    )

    # WHEN removing unwanted samples
    sample_sheet_creator.remove_unwanted_samples()

    # THEN the sample is not removed
    assert len(sample_sheet_creator.lims_samples) == 1


def test_remove_unwanted_samples_no_dual_index(
    novaseq6000_flow_cell_sample_no_dual_index: FlowCellSampleBcl2Fastq,
    novaseq_6000_flow_cell: FlowCellDirectoryData,
    caplog,
):
    """Test that samples with no dual index are removed."""
    # GIVEN a sample sheet creator with a sample without dual indexes
    sample_sheet_creator: SampleSheetCreatorBcl2Fastq = SampleSheetCreatorBcl2Fastq(
        flow_cell=novaseq_6000_flow_cell,
        lims_samples=[novaseq6000_flow_cell_sample_no_dual_index],
    )

    # WHEN removing unwanted samples
    sample_sheet_creator.remove_unwanted_samples()

    # THEN the only sample is removed
    assert len(sample_sheet_creator.lims_samples) == 0
    assert (
        f"Removing sample {novaseq6000_flow_cell_sample_no_dual_index} since it does not have dual index"
        in caplog.text
    )


def test_add_override_cycles_to_novaseqx_samples(
    novaseq_x_flow_cell: FlowCellDirectoryData,
    bcl_convert_samples_with_updated_indexes: list[FlowCellSampleBCLConvert],
    override_cycles_for_novaseq_x_samples: list[str],
):
    """Test that OverrideCycles values are generated correctly for NovaSeqX samples."""
    # GIVEN a SampleSheetCreator with samples without Override Cycles added
    sample_sheet_creator = SampleSheetCreatorBCLConvert(
        flow_cell=novaseq_x_flow_cell, lims_samples=bcl_convert_samples_with_updated_indexes
    )
    assert all(sample.override_cycles == "" for sample in sample_sheet_creator.lims_samples)

    # WHEN adding the correct values of override samples
    sample_sheet_creator.add_override_cycles_to_samples()

    # THEN the Override Cycles attribute is added to all samples
    assert all(
        sample.override_cycles == override_cycles_value
        for sample, override_cycles_value in zip(
            sample_sheet_creator.lims_samples,
            override_cycles_for_novaseq_x_samples,
        )
    )


def test_update_barcode_mismatch_values_for_samples(
    novaseq_x_flow_cell: FlowCellDirectoryData,
    bcl_convert_samples_with_updated_indexes: list[FlowCellSampleBCLConvert],
    barcode_mismatch_values_for_samples_with_updated_indexes: list[tuple[int, int]],
):
    """Tests that the barcode mismatch values are updated correctly for NovaSeqX samples."""
    # GIVEN a sample sheet creator with samples with barcode mismatch values equal to 1
    sample_sheet_creator = SampleSheetCreatorBCLConvert(
        flow_cell=novaseq_x_flow_cell, lims_samples=bcl_convert_samples_with_updated_indexes
    )
    assert all(
        sample.barcode_mismatches_1 == 1 and sample.barcode_mismatches_2 == 1
        for sample in sample_sheet_creator.lims_samples
    )

    # WHEN updating the barcode mismatch values
    sample_sheet_creator.update_barcode_mismatch_values_for_samples(
        sample_sheet_creator.lims_samples
    )

    # THEN exactly two samples have barcode mismatches equal to zero
    for sample, barcode_mismatch_tuple in zip(
        sample_sheet_creator.lims_samples, barcode_mismatch_values_for_samples_with_updated_indexes
    ):
        assert (sample.barcode_mismatches_1, sample.barcode_mismatches_2) == barcode_mismatch_tuple


@pytest.mark.parametrize(
    "flow_cell, correct_settings",
    [
        ("novaseq_6000_pre_1_5_kits_flow_cell_data", NO_REVERSE_COMPLEMENTS),
        ("novaseq_6000_post_1_5_kits_flow_cell_data", NOVASEQ_6000_POST_1_5_KITS),
        ("novaseq_x_flow_cell_data", NOVASEQ_X_INDEX_SETTINGS),
    ],
)
def test_get_index_settings(
    bcl_convert_sample_sheet_creator: SampleSheetCreatorBCLConvert,
    correct_settings: IndexSettings,
    flow_cell: str,
    request: FixtureRequest,
):
    """Test that the correct index settings are returned for each NovaSeq flow cell type."""
    # GIVEN run parameters for a flow cell
    flow_cell: FlowCellDirectoryData = request.getfixturevalue(flow_cell)
    bcl_convert_sample_sheet_creator.run_parameters = flow_cell.run_parameters
    # WHEN getting the index settings
    settings: IndexSettings = bcl_convert_sample_sheet_creator._get_index_settings()
    # THEN the correct index settings are returned
    assert settings == correct_settings


@pytest.mark.parametrize(
    "flow_cell, expected_result",
    [
        ("novaseq_6000_pre_1_5_kits_flow_cell_data", False),
        ("novaseq_6000_post_1_5_kits_flow_cell_data", True),
    ],
)
def test_is_novaseq6000_post_1_5_kit(
    bcl_convert_sample_sheet_creator: SampleSheetCreatorBCLConvert,
    flow_cell: str,
    expected_result: bool,
    request: FixtureRequest,
):
    """Test that the correct index settings are returned for each NovaSeq flow cell type."""
    # GIVEN run parameters for a flow cell
    flow_cell: FlowCellDirectoryData = request.getfixturevalue(flow_cell)
    bcl_convert_sample_sheet_creator.run_parameters = flow_cell.run_parameters
    # WHEN getting checking if the flow cell was sequenced after the NovaSeq 6000 1.5 kits
    result: bool = bcl_convert_sample_sheet_creator._is_novaseq6000_post_1_5_kit
    # THEN the correct index settings are returned
    assert result == expected_result
