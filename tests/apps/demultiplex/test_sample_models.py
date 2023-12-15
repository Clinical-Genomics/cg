from typing import Type
from unittest.mock import Mock

import pytest

from cg.apps.demultiplex.sample_sheet.index import (
    INDEX_ONE_PAD_SEQUENCE,
    INDEX_TWO_PAD_SEQUENCE,
    LONG_INDEX_CYCLE_NR,
    SHORT_SAMPLE_INDEX_LENGTH,
)
from cg.apps.demultiplex.sample_sheet.sample_models import (
    FlowCellSample,
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.constants.demultiplexing import IndexSettings
from cg.models.demultiplex.run_parameters import RunParameters


@pytest.mark.parametrize(
    "lims_index, expected_index_1, expected_index2",
    [
        ("CCATTCGANNNNNNNNN-GTTGTCCG", "CCATTCGA", "GTTGTCCG"),
        ("CGATAGCAGG-AATGCTACGA", "CGATAGCAGG", "AATGCTACGA"),
        ("ACAGCAAG", "ACAGCAAG", ""),
        ("ACAGCAAG-", "ACAGCAAG", ""),
        ("ATAGCAGG-AATGCTAC\n", "ATAGCAGG", "AATGCTAC"),
    ],
    ids=[
        "17-nt index1",
        "equal-length indexes",
        "single index",
        "single index with dash",
        "index with newline",
    ],
)
def test_separate_indexes(lims_index: str, expected_index_1: str, expected_index2: str):
    """Test that the different kind of lims indexes are parsed correctly as index and index2."""
    # GIVEN a sample sheet with a single sample on one lane
    sample = FlowCellSampleBCLConvert(lane=1, index=lims_index, sample_id="ACC123")

    # WHEN separating the index
    sample.separate_indexes()

    # THEN the index should be separated
    assert sample.index == expected_index_1
    assert sample.index2 == expected_index2


@pytest.mark.parametrize(
    "needs_reverse_complement, expected_index2",
    [
        (True, f"{INDEX_TWO_PAD_SEQUENCE}GCCAAGGT"),
        (False, f"GCCAAGGT{INDEX_TWO_PAD_SEQUENCE}"),
    ],
    ids=["reverse complement", "no reverse complement"],
)
def test_pad_indexes_needs_padding(needs_reverse_complement: bool, expected_index2: str):
    """Test that indexes that need to be padded are padded with and without reverse complement."""
    # GIVEN a run parameters file with 10-nt indexes with an i5 that needs reverse complementing
    mock_index_settings = Mock(
        spec=IndexSettings, should_i5_be_reverse_complimented=needs_reverse_complement
    )
    mock_run_parameters = Mock(
        spec=RunParameters,
        get_index_1_cycles=Mock(return_value=10),
        get_index_2_cycles=Mock(return_value=10),
        index_settings=mock_index_settings,
    )

    # GIVEN a FlowCellSampleBcl2Fastq with 8-nt indexes
    sample = FlowCellSampleBcl2Fastq(
        lane=1, index="GTCTACAC-GCCAAGGT", sample_id="ACC123", project="project", sample_name="name"
    )
    sample.separate_indexes()

    # WHEN padding the indexes
    sample._pad_indexes_if_necessary(run_parameters=mock_run_parameters)

    # THEN the indexes were correctly padded
    assert_correct_padding(
        sample=sample,
        index_length=LONG_INDEX_CYCLE_NR,
        index1_value=f"GTCTACAC{INDEX_ONE_PAD_SEQUENCE}",
        index2_value=expected_index2,
    )


def assert_correct_padding(
    sample: FlowCellSampleBcl2Fastq, index_length: int, index1_value: str, index2_value: str
):
    """Assert that the indexes have the correct length and are correctly padded."""
    assert len(sample.index) == index_length
    assert sample.index == index1_value
    # THEN the second index was correctly padded
    assert len(sample.index2) == index_length
    assert sample.index2 == index2_value


def test_pad_indexes_no_padding():
    """Test that indexes that do not need to be padded are not padded."""
    # GIVEN a RunParameters with 8-nt indexes
    mock_run_parameters = Mock(
        spec=RunParameters,
        get_index_1_cycles=Mock(return_value=8),
        get_index_2_cycles=Mock(return_value=8),
    )

    # GIVEN a FlowCellSampleBcl2Fastq with 8-nt indexes
    initial_index1: str = "GTCTACAC"
    initial_index2: str = "GCCAAGGT"
    sample = FlowCellSampleBcl2Fastq(
        lane=1,
        index=f"{initial_index1}-{initial_index2}",
        sample_id="ACC123",
        project="project",
        sample_name="name",
    )
    sample.separate_indexes()

    # WHEN trying to pad the indexes
    sample._pad_indexes_if_necessary(run_parameters=mock_run_parameters)

    # THEN the indexes were not padded
    assert_correct_padding(
        sample=sample,
        index_length=SHORT_SAMPLE_INDEX_LENGTH,
        index1_value=initial_index1,
        index2_value=initial_index2,
    )


@pytest.mark.parametrize(
    "raw_index, index1_cycles, expected_parsed_cycles",
    [("CGATAGCAGG", 10, "I10;"), ("GTTCCAAT", 8, "I8;"), ("GTTCCAAT", 10, "I8N2;")],
    ids=["10-nt index and cycles", "8-nt index and cycles", "8-ny index, 10-ny cycles"],
)
def test_get_index1_override_cycles(
    raw_index: str, index1_cycles: int, expected_parsed_cycles: str
):
    """Test that the returned index 1 cycles is teh expected for different index configurations."""
    # GIVEN a FlowCellSampleBCLConvert with an index
    sample = FlowCellSampleBCLConvert(lane=1, index=raw_index, sample_id="ACC123")

    # WHEN getting the index1 override cycles
    index1_cycles: str = sample._get_index1_override_cycles(len_index1_cycles=index1_cycles)

    # THEN the index1 override cycles value is the expected one
    assert index1_cycles == expected_parsed_cycles


@pytest.mark.parametrize(
    "raw_index, index2_cycles, reverse_cycle, expected_parsed_cycles",
    [
        ("CGATAGCAGG-AATGCTACGA", 10, None, "I10;"),
        ("GTTCCAAT-AATTCTGC", 8, None, "I8;"),
        ("CGATAGCAGG", 10, None, "N10;"),
        ("GTTCCAAT", 8, None, "N8;"),
        ("GTTCCAAT-AATTCTGC", 10, True, "N2I8;"),
        ("GTTCCAAT-AATTCTGC", 10, False, "I8N2;"),
        ("GTTCCAAT-AATTCTGC", 0, None, ""),
    ],
    ids=[
        "10-nt index and cycles",
        "8-nt index and cycles",
        "No index, 10-nt cycles",
        "No index, 8-nt cycles",
        "8-nt index, 10-nt cycles reversed",
        "8-nt index, 10-nt cycles not reversed",
        "No cycles",
    ],
)
def test_get_index2_override_cycles(
    raw_index: str, index2_cycles: int, reverse_cycle: bool, expected_parsed_cycles: str
):
    """Test that the returned index 2 cycles is the expected for different index configurations."""
    # GIVEN a FlowCellSampleBCLConvert with separated indexes
    sample = FlowCellSampleBCLConvert(lane=1, index=raw_index, sample_id="ACC123")
    sample.separate_indexes()

    # WHEN getting the index2 override cycles
    index2_cycles: str = sample._get_index2_override_cycles(
        len_index2_cycles=index2_cycles, reverse_cycle=reverse_cycle
    )

    # THEN the index2 override cycles value is the expected one
    assert index2_cycles == expected_parsed_cycles


def test_update_override_cycles():
    # TODO: Parametrise this test with different run parameter files and samples
    """."""
    # GIVEN a run parameters object

    # GIVEN a FlowCellSampleBCLConvert

    # WHEN updating the override cycles

    # THEN the override cycles are updated with the expected value


@pytest.mark.parametrize(
    "sample_list_fixture, expected_barcode_mismatch",
    [("bcl_convert_samples_similar_index1", 0), ("bcl_convert_samples_similar_index2", 1)],
    ids=["barcode1_0", "barcode1_1"],
)
def test_update_barcode_mismatches_1(
    sample_list_fixture: str, expected_barcode_mismatch: int, request: pytest.FixtureRequest
):
    """Test that index 1 barcode mismatch values are as expected for different sets of samples."""
    # GIVEN a list of FlowCellSampleBCLConvert
    sample_list: list[FlowCellSampleBCLConvert] = request.getfixturevalue(sample_list_fixture)

    # GIVEN a FlowCellSampleBCLConvert
    sample_to_update: FlowCellSampleBCLConvert = sample_list[0]

    # WHEN updating the barcode mismatches 1
    sample_to_update.update_barcode_mismatches_1(samples_to_compare=sample_list)

    # THEN the barcode mismatches 1 are updated with the expected value
    assert sample_to_update.barcode_mismatches_1 == expected_barcode_mismatch


@pytest.mark.parametrize(
    "sample_list_fixture, expected_barcode_mismatch",
    [("bcl_convert_samples_similar_index1", 1), ("bcl_convert_samples_similar_index2", 0)],
    ids=["barcode2_0", "barcode2_1"],
)
def test_update_barcode_mismatches_2(
    sample_list_fixture: str, expected_barcode_mismatch: int, request: pytest.FixtureRequest
):
    # TODO: Parametrise this test with different sets of samples and expected outputs:
    #  One that is, one that is 1 and one that is 'na'
    """Test that index 2 barcode mismatch values are as expected for different sets of samples."""
    # GIVEN a list of FlowCellSampleBCLConvert
    sample_list: list[FlowCellSampleBCLConvert] = request.getfixturevalue(sample_list_fixture)

    # GIVEN a FlowCellSampleBCLConvert
    sample_to_update: FlowCellSampleBCLConvert = sample_list[0]

    # WHEN updating the barcode mismatches 2
    sample_to_update.update_barcode_mismatches_2(samples_to_compare=sample_list)

    # THEN the barcode mismatches 1 are updated with the expected value
    assert sample_to_update.barcode_mismatches_2 == expected_barcode_mismatch


@pytest.mark.parametrize(
    "run_parameters_fixture, raw_lims_samples_fixture",
    [
        ("novaseq_x_run_parameters", "novaseq_x_lims_samples"),
        ("novaseq_6000_run_parameters_pre_1_5_kits", "novaseq_6000_pre_1_5_kits_lims_samples"),
        ("novaseq_6000_run_parameters_post_1_5_kits", "novaseq_6000_post_1_5_kits_lims_samples"),
        ("hiseq_x_run_parameters_single_index", "hiseq_x_lims_samples"),
        ("hiseq_2500_run_parameters_double_index", "hiseq_2500_lims_samples"),
    ],
    ids=[
        "NovaSeqX",
        "NovaSeq6000 pre1.5",
        "NovaSeq6000 post1.5",
        "HiSeqX",
        "HiSeq2500",
    ],
)
def test_process_sample_for_sample_sheet_bcl_convert(
    run_parameters_fixture: str, raw_lims_samples_fixture: str, request: pytest.FixtureRequest
):
    # TODO: We need a raw FlowCellSampleBCLConvert
    """."""
    # GIVEN a run parameters object and a list of BCLConvert samples from a flow cell
    run_parameters: RunParameters = request.getfixturevalue(run_parameters_fixture)
    raw_lims_samples: list[FlowCellSampleBCLConvert] = request.getfixturevalue(
        raw_lims_samples_fixture
    )

    # GIVEN a FlowCellSampleBCLConvert
    sample: FlowCellSampleBCLConvert = raw_lims_samples[0]

    # WHEN processing the sample for a sample sheet
    sample.process_sample_for_sample_sheet(run_parameters=run_parameters)

    # THEN the sample is processed
    assert sample.barcode_mismatches_1
    assert sample.barcode_mismatches_2
    assert sample.override_cycles
