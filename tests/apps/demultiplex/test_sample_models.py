import pytest

from cg.apps.demultiplex.sample_sheet.index import get_reverse_complement_dna_seq
from cg.apps.demultiplex.sample_sheet.sample_models import IlluminaSampleIndexSetting
from cg.constants.symbols import EMPTY_STRING
from cg.models.demultiplex.run_parameters import RunParameters


@pytest.mark.parametrize(
    "lims_sample",
    [
        {"index": "GTCTACAC-GCCAAGGT", "sample_id": "ACC123"},
        {"lane": 1, "sample_id": "ACC123"},
        {"lane": 1, "index": "GTCTACAC-GCCAAGGT"},
    ],
    ids=["no lane", "no index", "no sample id"],
)
def test_validate_inputs_bcl_convert_sample_missing_attribute(lims_sample: dict):
    """Test that validating a BCLConvert sample with a missing attribute fails."""
    # GIVEN a raw LIMS sample without a mandatory attribute

    # WHEN validating the sample
    with pytest.raises(AttributeError) as exc_info:
        IlluminaSampleIndexSetting.validate_inputs(lims_sample=lims_sample)

    # THEN a pydantic validation error is raised
    assert "validate_inputs" in str(exc_info.value)


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
def test_separate_indexes_dual_run(lims_index: str, expected_index_1: str, expected_index2: str):
    """Test that parsing different kinds of dual-run raw indexes as index and index2 works."""
    # GIVEN a sample sheet with a single sample on one lane
    sample = IlluminaSampleIndexSetting(lane=1, index=lims_index, sample_id="ACC123")

    # WHEN separating the index
    sample.separate_indexes(is_run_single_index=False)

    # THEN the index should be separated
    assert sample.index == expected_index_1
    assert sample.index2 == expected_index2


def test_separate_indexes_single_run(
    index1_8_nt_sequence_from_lims: str, bcl_convert_flow_cell_sample: IlluminaSampleIndexSetting
):
    """Test index2 is ignored when parsing a double index in a single index run."""
    # GIVEN a sample with a double index

    # WHEN separating the index
    bcl_convert_flow_cell_sample.separate_indexes(is_run_single_index=True)

    # THEN the index should be separated
    assert bcl_convert_flow_cell_sample.index == index1_8_nt_sequence_from_lims
    assert bcl_convert_flow_cell_sample.index2 == EMPTY_STRING


@pytest.mark.parametrize(
    "run_parameters_fixture",
    [
        "hiseq_x_single_index_run_parameters",
        "hiseq_x_dual_index_run_parameters",
        "hiseq_2500_dual_index_run_parameters",
        "hiseq_2500_custom_index_run_parameters",
        "novaseq_6000_run_parameters_pre_1_5_kits",
        "novaseq_6000_run_parameters_post_1_5_kits",
        "novaseq_x_run_parameters",
    ],
)
def test_update_override_cycles(
    bcl_convert_flow_cell_sample: IlluminaSampleIndexSetting,
    run_parameters_fixture: str,
    request: pytest.FixtureRequest,
):
    """Test that updating a sample's override cycles works for different run parameters objects."""
    # GIVEN a run parameters object
    run_parameters: RunParameters = request.getfixturevalue(run_parameters_fixture)

    # GIVEN a FlowCellSampleBCLConvert without override cycles
    assert bcl_convert_flow_cell_sample.override_cycles == EMPTY_STRING

    # WHEN updating the override cycles
    bcl_convert_flow_cell_sample.update_override_cycles(run_parameters=run_parameters)

    # THEN the override cycles are updated with the expected value
    cycles: list[str] = bcl_convert_flow_cell_sample.override_cycles.split(";")
    assert len(cycles) >= 3
    assert cycles[0] == f"Y{run_parameters.get_read_1_cycles()}"
    assert cycles[-1] == f"Y{run_parameters.get_read_2_cycles()}"
    assert "I" in cycles[1]


@pytest.mark.parametrize(
    "sample_list_fixture, expected_barcode_mismatch",
    [("bcl_convert_samples_similar_index1", 0), ("bcl_convert_samples_similar_index2", 1)],
    ids=["barcode1_0", "barcode1_1"],
)
def test_update_barcode_mismatches_1(
    sample_list_fixture: str, expected_barcode_mismatch: int, request: pytest.FixtureRequest
):
    """Test that index 1 barcode mismatches values are as expected for different sets of samples."""
    # GIVEN a list of FlowCellSampleBCLConvert
    sample_list: list[IlluminaSampleIndexSetting] = request.getfixturevalue(sample_list_fixture)

    # GIVEN a FlowCellSampleBCLConvert
    sample_to_update: IlluminaSampleIndexSetting = sample_list[0]

    # WHEN updating the value for index 1 barcode mismatches
    sample_to_update._update_barcode_mismatches_1(samples_to_compare=sample_list)

    # THEN the value for index 1 barcode mismatches is updated with the expected value
    assert sample_to_update.barcode_mismatches_1 == expected_barcode_mismatch


@pytest.mark.parametrize(
    "sample_list_fixture, expected_barcode_mismatch",
    [("bcl_convert_samples_similar_index1", 1), ("bcl_convert_samples_similar_index2", 0)],
    ids=["barcode2_0", "barcode2_1"],
)
def test_update_barcode_mismatches_2(
    sample_list_fixture: str, expected_barcode_mismatch: int, request: pytest.FixtureRequest
):
    """Test that index 2 barcode mismatches values are as expected for different sets of samples."""
    # GIVEN a list of FlowCellSampleBCLConvert
    sample_list: list[IlluminaSampleIndexSetting] = request.getfixturevalue(sample_list_fixture)

    # GIVEN a FlowCellSampleBCLConvert
    sample_to_update: IlluminaSampleIndexSetting = sample_list[0]

    # WHEN updating the value for index 2 barcode mismatches
    sample_to_update._update_barcode_mismatches_2(
        samples_to_compare=sample_list, is_reverse_complement=False
    )

    # THEN the value for index 2 barcode mismatches is updated with the expected value
    assert sample_to_update.barcode_mismatches_2 == expected_barcode_mismatch


@pytest.mark.parametrize(
    "run_parameters_fixture, raw_lims_samples_fixture",
    [
        ("novaseq_x_run_parameters", "novaseq_x_lims_samples"),
        (
            "novaseq_6000_run_parameters_pre_1_5_kits",
            "novaseq_6000_pre_1_5_kits_bcl_convert_lims_samples",
        ),
        (
            "novaseq_6000_run_parameters_post_1_5_kits",
            "novaseq_6000_post_1_5_kits_bcl_convert_lims_samples",
        ),
        ("hiseq_x_single_index_run_parameters", "hiseq_x_single_index_bcl_convert_lims_samples"),
        ("hiseq_x_dual_index_run_parameters", "hiseq_x_dual_index_bcl_convert_lims_samples"),
        ("hiseq_2500_dual_index_run_parameters", "hiseq_2500_dual_index_bcl_convert_lims_samples"),
        (
            "hiseq_2500_custom_index_run_parameters",
            "hiseq_2500_custom_index_bcl_convert_lims_samples",
        ),
    ],
    ids=[
        "NovaSeqX",
        "NovaSeq6000 pre1.5",
        "NovaSeq6000 post1.5",
        "HiSeqX single index",
        "HiSeqX dual index",
        "HiSeq2500 dual index",
        "HiSeq2500 custom index",
    ],
)
def test_process_indexes_for_sample_sheet_bcl_convert(
    run_parameters_fixture: str, raw_lims_samples_fixture: str, request: pytest.FixtureRequest
):
    """Test that indexes are processed correctly for a BCLConvert sample."""
    # GIVEN a run parameters object and a list of BCLConvert samples from a flow cell
    run_parameters: RunParameters = request.getfixturevalue(run_parameters_fixture)
    raw_lims_samples: list[IlluminaSampleIndexSetting] = request.getfixturevalue(
        raw_lims_samples_fixture
    )

    # GIVEN a FlowCellSampleBCLConvert
    sample: IlluminaSampleIndexSetting = raw_lims_samples[0]

    # WHEN processing the sample for a sample sheet
    sample.process_indexes(run_parameters=run_parameters)

    # THEN the sample is processed correctly
    assert "-" not in sample.index
    assert sample.override_cycles != EMPTY_STRING


@pytest.mark.parametrize(
    "run_parameters_fixture, expected_index2",
    [
        ("hiseq_x_single_index_run_parameters", ""),
        ("hiseq_x_dual_index_run_parameters", "GCCAAGGT"),
        ("hiseq_2500_dual_index_run_parameters", "GCCAAGGT"),
        ("hiseq_2500_custom_index_run_parameters", "GCCAAGGT"),
        ("novaseq_6000_run_parameters_pre_1_5_kits", "GCCAAGGT"),
        ("novaseq_6000_run_parameters_post_1_5_kits", get_reverse_complement_dna_seq("GCCAAGGT")),
        ("novaseq_x_run_parameters", "GCCAAGGT"),
    ],
    ids=[
        "HiSeqX single index",
        "HiSeqX dual index",
        "HiSeq2500 dual index",
        "HiSeq2500 custom index",
        "NovaSeq6000 pre1.5",
        "NovaSeq6000 post1.5",
        "NovaSeqX",
    ],
)
def test_process_indexes_bcl_convert(
    bcl_convert_flow_cell_sample: IlluminaSampleIndexSetting,
    run_parameters_fixture: str,
    expected_index2: str,
    request: pytest.FixtureRequest,
):
    """Test that processing indexes of a BCLConvert sample from different sequencers work."""
    # GIVEN a run parameters object
    run_parameters: RunParameters = request.getfixturevalue(run_parameters_fixture)

    # GIVEN a FlowCellSampleBclConvert with 8-nt indexes

    # WHEN processing the sample for a sample sheet
    bcl_convert_flow_cell_sample.process_indexes(run_parameters=run_parameters)

    # THEN the sample indexes and override cycles are processed
    assert bcl_convert_flow_cell_sample.index2 == expected_index2
    assert bcl_convert_flow_cell_sample.override_cycles != EMPTY_STRING
