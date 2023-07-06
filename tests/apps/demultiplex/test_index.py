"""Tests for functions related to indexes."""
from typing import Dict, List, Set, Tuple

import pytest

from cg.apps.demultiplex.sample_sheet.index import (
    INDEX_ONE_PAD_SEQUENCE,
    INDEX_TWO_PAD_SEQUENCE,
    LONG_INDEX_CYCLE_NR,
    Index,
    adapt_indexes_for_sample,
    get_hamming_distance_for_indexes,
    get_index_pair,
    get_indexes_by_lane,
    get_reagent_kit_version,
    get_reverse_complement_dna_seq,
    get_valid_indexes,
    index_exists,
    is_reverse_complement,
    update_barcode_mismatch_values_for_sample,
)
from cg.apps.demultiplex.sample_sheet.models import (
    FlowCellSampleNovaSeq6000Bcl2Fastq,
    FlowCellSampleNovaSeqX,
)
from cg.models.demultiplex.run_parameters import RunParameters


def test_get_valid_indexes():
    """Test that the function get_valid_indexes returns a list of Index objects."""
    # GIVEN a sample sheet API

    # WHEN fetching the indexes
    indexes: List[Index] = get_valid_indexes()

    # THEN assert that the indexes are correct
    assert indexes
    assert isinstance(indexes[0], Index)


def test_index_exists_for_existing_index(valid_index: Index):
    """Test that checking the existence of an existent index returns true."""
    # GIVEN a list of indexes
    indexes: Set[str] = set(index.sequence for index in get_valid_indexes())
    # GIVEN an existent index
    existent_index: str = valid_index.sequence

    # WHEN testing for the existence of the index

    # THEN the test returns true
    assert index_exists(index=existent_index, indexes=indexes)


def test_index_exists_for_non_existent_index():
    """Test that checking the existence of a non-existent index returns false."""
    # GIVEN a list of indexes
    indexes: Set[str] = set(index.sequence for index in get_valid_indexes())
    # GIVEN a non-existent index
    non_existent_index: str = "non-existent-index"

    # WHEN testing for the existence of the index

    # THEN the test returns false
    assert not index_exists(index=non_existent_index, indexes=indexes)


def test_get_indexes_by_lane(
    novaseq6000_flow_cell_sample_1: FlowCellSampleNovaSeq6000Bcl2Fastq,
    novaseq6000_flow_cell_sample_2: FlowCellSampleNovaSeq6000Bcl2Fastq,
):
    """Test that getting indexes by lane groups indexes correctly."""
    # GIVEN two samples on different lanes
    assert novaseq6000_flow_cell_sample_1.lane != novaseq6000_flow_cell_sample_2.lane

    # WHEN getting indexes by lane
    indexes_by_lane: Dict[int, Set[str]] = get_indexes_by_lane(
        samples=[novaseq6000_flow_cell_sample_1, novaseq6000_flow_cell_sample_2]
    )

    # THEN the result dictionary has two items
    assert len(indexes_by_lane.keys()) == 2
    assert len(indexes_by_lane.values()) == 2


def test_get_reagent_kit_version_non_existent_reagent(caplog):
    """Test that getting a non-existent reagent kit version fails."""
    # GIVEN a non-existent reagent kit version
    non_existent_reagent: str = "reagent_does_not_exist"

    # WHEN getting the reagent kit version
    with pytest.raises(SyntaxError):
        get_reagent_kit_version(reagent_kit_version=non_existent_reagent)
        # THEN an error is raised
        assert caplog.text == f"Unknown reagent kit version {non_existent_reagent}"


def test_get_reagent_kit_version_all_possible_versions():
    """Test that get_reagent_kit_version works with the valid versions."""
    # GIVEN the valid reagent kit versions
    valid_versions: List[str] = ["1", "3"]
    valid_outputs: List = []

    # WHEN getting the reagent kit versions of the inputs
    for version in valid_versions:
        valid_outputs.append(get_reagent_kit_version(reagent_kit_version=version))

    # THEN the output versions are valid
    assert valid_outputs == ["1.0", "1.5"]


def test_get_index_pair_valid_cases(
    novaseq6000_flow_cell_sample_before_adapt_indexes: FlowCellSampleNovaSeq6000Bcl2Fastq,
):
    """Test that getting individual indexes from valid dual indexes works."""
    # GIVEN a list of dual indexes and their correct separation into individual indexes
    dual_indexes: List[str] = ["ABC-DEF", "   GHI - JKL   ", "MNO-PQR\n"]
    expected_results: List[Tuple[str, str]] = [("ABC", "DEF"), ("GHI", "JKL"), ("MNO", "PQR")]

    # WHEN getting the individual indexes of the valid indexes
    for index, expected in zip(dual_indexes, expected_results):
        novaseq6000_flow_cell_sample_before_adapt_indexes.index = index
        # THEN the result is the expected result for all cases
        assert get_index_pair(sample=novaseq6000_flow_cell_sample_before_adapt_indexes) == expected


def test_get_reverse_complement():
    """Test that getting the reverse complement of a DNA strain returns the correct sequence."""
    # GIVEN a DNA strain and its reverse complement
    dna_strain: str = "ACCTCTGT"
    reversed_complement: str = "ACAGAGGT"

    # WHEN getting the reverse complement of the DNA strain
    returned_reverse_complement: str = get_reverse_complement_dna_seq(dna=dna_strain)

    # THEN the result is the expected
    assert returned_reverse_complement == reversed_complement


def test_get_reverse_complement_not_dna(caplog):
    """Test that using a string without 'A', 'C', 'G' or 'T' fails."""
    # GIVEN a non-DNA strain
    strain: str = "ACCUCTGU"

    # WHEN getting the reverse complement
    with pytest.raises(KeyError):
        # THEN the process fails due to not recognising the unknown nucleotide
        get_reverse_complement_dna_seq(dna=strain)


def test_adapt_barcode_mismatch_values(
    lims_novaseq_x_samples: List[FlowCellSampleNovaSeqX],
    novaseq_x_flow_cell_sample_before_adapt_indexes: FlowCellSampleNovaSeqX,
):
    """Test that the barcode mismatch values are updated for a sample."""
    # GIVEN a list of NovaSeqX samples
    present_index: str = lims_novaseq_x_samples[0].index
    # GIVEN a sample
    novaseq_x_flow_cell_sample_before_adapt_indexes.index = present_index
    assert novaseq_x_flow_cell_sample_before_adapt_indexes.barcode_mismatches_1 == 1
    assert novaseq_x_flow_cell_sample_before_adapt_indexes.barcode_mismatches_2 == 1

    # WHEN adapting the barcode mismatch values
    update_barcode_mismatch_values_for_sample(
        sample_to_update=novaseq_x_flow_cell_sample_before_adapt_indexes,
        samples_to_compare_to=lims_novaseq_x_samples,
    )

    # THEN the barcode mismatch values have been updated
    assert novaseq_x_flow_cell_sample_before_adapt_indexes.barcode_mismatches_1 == 0
    assert novaseq_x_flow_cell_sample_before_adapt_indexes.barcode_mismatches_2 == 0


def test_adapt_barcode_mismatch_values_repeated_sample(
    novaseq_x_flow_cell_sample_before_adapt_indexes: FlowCellSampleNovaSeqX,
):
    """Test that a sample does not compare to itself when adapting barcode mismatching values."""
    # GIVEN a list of repeated unadapted NovaSeqX samples
    assert novaseq_x_flow_cell_sample_before_adapt_indexes.barcode_mismatches_1 == 1
    assert novaseq_x_flow_cell_sample_before_adapt_indexes.barcode_mismatches_2 == 1
    samples: List[FlowCellSampleNovaSeqX] = [
        novaseq_x_flow_cell_sample_before_adapt_indexes for _ in range(3)
    ]

    # WHEN adapting the barcode mismatch values for the samples
    update_barcode_mismatch_values_for_sample(
        sample_to_update=novaseq_x_flow_cell_sample_before_adapt_indexes,
        samples_to_compare_to=samples,
    )

    # THEN the barcode mismatch values remains being 1 for all samples
    for sample in samples:
        assert sample.barcode_mismatches_1 == 1
        assert sample.barcode_mismatches_2 == 1


def test_adapt_indexes_for_sample_reverse_complement_padding(
    novaseq_6000_run_parameters: RunParameters,
    novaseq6000_flow_cell_sample_before_adapt_indexes: FlowCellSampleNovaSeq6000Bcl2Fastq,
):
    """Test that adapting indexes for a sample that needs padding and reverse complement works."""
    # GIVEN a run parameters file that needs reverse complement of indexes
    assert is_reverse_complement(run_parameters=novaseq_6000_run_parameters)
    # GIVEN a sample that needs padding
    sample: FlowCellSampleNovaSeq6000Bcl2Fastq = novaseq6000_flow_cell_sample_before_adapt_indexes
    assert novaseq_6000_run_parameters.get_index_1_cycles() == LONG_INDEX_CYCLE_NR
    sample.index = "ATTCCACA-TGGTCTTG"

    # WHEN adapting the indexes of the sample
    adapt_indexes_for_sample(
        sample=sample,
        index_cycles=novaseq_6000_run_parameters.index_length,
        reverse_complement=is_reverse_complement(run_parameters=novaseq_6000_run_parameters),
    )

    # THEN the first index was correctly adapted
    assert len(sample.index) == LONG_INDEX_CYCLE_NR
    assert sample.index[-2:] == INDEX_ONE_PAD_SEQUENCE
    # THEN the second index was correctly adapted
    assert len(sample.index2) == LONG_INDEX_CYCLE_NR
    assert sample.index2[-2:] == get_reverse_complement_dna_seq(dna=INDEX_TWO_PAD_SEQUENCE)


def test_adapt_indexes_for_sample_reverse_complement_no_padding(
    novaseq_6000_run_parameters: RunParameters,
    novaseq6000_flow_cell_sample_before_adapt_indexes: FlowCellSampleNovaSeq6000Bcl2Fastq,
):
    """Test that adapting indexes of a sample that needs reverse complement but no padding works."""
    # GIVEN a run parameters file that needs reverse complement of indexes
    assert is_reverse_complement(run_parameters=novaseq_6000_run_parameters)
    # GIVEN a sample that does not need padding
    sample: FlowCellSampleNovaSeq6000Bcl2Fastq = novaseq6000_flow_cell_sample_before_adapt_indexes
    assert novaseq_6000_run_parameters.get_index_1_cycles() == LONG_INDEX_CYCLE_NR
    assert len(sample.index) >= 2 * LONG_INDEX_CYCLE_NR
    initial_indexes: List[str] = sample.index.split("-")
    initial_index1: str = initial_indexes[0]
    initial_index2: str = initial_indexes[1]

    # WHEN adapting the indexes of the sample
    adapt_indexes_for_sample(
        sample=sample,
        index_cycles=novaseq_6000_run_parameters.index_length,
        reverse_complement=is_reverse_complement(run_parameters=novaseq_6000_run_parameters),
    )

    # THEN the first index was correctly adapted
    assert len(sample.index) == LONG_INDEX_CYCLE_NR
    assert sample.index == initial_index1
    # THEN the second index was correctly adapted
    assert len(sample.index2) == LONG_INDEX_CYCLE_NR
    assert sample.index2 == get_reverse_complement_dna_seq(dna=initial_index2)


def test_adapt_indexes_for_sample_no_reverse_complement_no_padding(
    novaseq_x_run_parameters: RunParameters,
    novaseq_x_flow_cell_sample_before_adapt_indexes: FlowCellSampleNovaSeqX,
):
    """Test that adapting indexes of a sample that does not need reverse complement nor padding works."""
    # GIVEN a run parameters file that does not need reverse complement of indexes
    assert not is_reverse_complement(run_parameters=novaseq_x_run_parameters)
    # GIVEN a sample that does not need padding
    sample: FlowCellSampleNovaSeqX = novaseq_x_flow_cell_sample_before_adapt_indexes
    assert novaseq_x_run_parameters.get_index_1_cycles() == LONG_INDEX_CYCLE_NR
    assert len(sample.index) >= 2 * LONG_INDEX_CYCLE_NR
    initial_indexes: List[str] = sample.index.split("-")
    initial_index1: str = initial_indexes[0]
    initial_index2: str = initial_indexes[1]

    # WHEN adapting the indexes of the sample
    adapt_indexes_for_sample(
        sample=sample,
        index_cycles=novaseq_x_run_parameters.index_length,
        reverse_complement=is_reverse_complement(run_parameters=novaseq_x_run_parameters),
    )

    # THEN the first index was correctly adapted
    assert len(sample.index) == LONG_INDEX_CYCLE_NR
    assert sample.index == initial_index1
    # THEN the second index was correctly adapted
    assert len(sample.index2) == LONG_INDEX_CYCLE_NR
    assert sample.index2 == initial_index2


def test_get_hamming_distance_index_different_lengths():
    """Test that the hamming distance between indexes with same prefix but different lengths is zero."""
    # GIVEN two index_1 sequences with the same prefixes but different lengths
    sequence_1: str = "GATTACA"
    sequence_2: str = "GATTACAXX"

    # WHEN getting the hamming distance between them in any order

    # THEN the distance is zero
    assert get_hamming_distance_for_indexes(sequence_1=sequence_1, sequence_2=sequence_2) == 0
    assert get_hamming_distance_for_indexes(sequence_1=sequence_2, sequence_2=sequence_1) == 0

    # WHEN getting the hamming distance between themselves

    # THEN the distance is zero
    assert get_hamming_distance_for_indexes(sequence_1=sequence_1, sequence_2=sequence_1) == 0
    assert get_hamming_distance_for_indexes(sequence_1=sequence_2, sequence_2=sequence_2) == 0


def test_get_hamming_distance_index_different_prefixes():
    """Test that the hamming distance between indexes with different prefixes is greater than zero."""
    # GIVEN two index_1 sequences with the same suffixes but different prefixes
    sequence_1: str = "GATTACA"
    sequence_2: str = "XXGATTACA"

    # WHEN getting the hamming distance between them in any order

    # THEN the distance is greater than zero
    assert get_hamming_distance_for_indexes(sequence_1=sequence_1, sequence_2=sequence_2) > 0
    assert get_hamming_distance_for_indexes(sequence_1=sequence_2, sequence_2=sequence_1) > 0
