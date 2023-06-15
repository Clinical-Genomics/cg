"""Tests for functions related to indexes."""
from typing import Dict, List, Set

import pytest

from cg.apps.demultiplex.sample_sheet.index import (
    Index,
    INDEX_ONE_PAD_SEQUENCE,
    INDEX_TWO_PAD_SEQUENCE,
    LONG_INDEX_CYCLE_NR,
    adapt_indexes,
    is_reverse_complement,
    get_valid_indexes,
    get_indexes_by_lane,
    get_reagent_kit_version,
    get_reverse_complement_dna_seq,
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


def test_adapt_indexes_reverse_complement_padding(
    novaseq_6000_run_parameters: RunParameters,
    novaseq6000_flow_cell_sample_before_adapt_indexes: FlowCellSampleNovaSeq6000Bcl2Fastq,
):
    """Test that adapting indexes of a sample that needs padding and reverse complement works."""
    # GIVEN a run parameters file that needs reverse complement of indexes
    assert is_reverse_complement(run_parameters=novaseq_6000_run_parameters)
    # GIVEN a sample that needs padding
    assert novaseq_6000_run_parameters.get_index_1_cycles() == LONG_INDEX_CYCLE_NR
    novaseq6000_flow_cell_sample_before_adapt_indexes.index = "ATTCCACA-TGGTCTTG"
    samples: List = [novaseq6000_flow_cell_sample_before_adapt_indexes]

    # WHEN adapting the indexes of the sample
    adapt_indexes(samples=samples, run_parameters=novaseq_6000_run_parameters)
    test_sample: FlowCellSampleNovaSeq6000Bcl2Fastq = samples[0]

    # THEN the first index was correctly adapted
    assert len(test_sample.index) == LONG_INDEX_CYCLE_NR
    assert test_sample.index[-2:] == INDEX_ONE_PAD_SEQUENCE
    # THEN the second index was correctly adapted
    assert len(test_sample.index2) == LONG_INDEX_CYCLE_NR
    assert test_sample.index2[-2:] == get_reverse_complement_dna_seq(dna=INDEX_TWO_PAD_SEQUENCE)


def test_adapt_indexes_reverse_complement_no_padding(
    novaseq_6000_run_parameters: RunParameters,
    novaseq6000_flow_cell_sample_before_adapt_indexes: FlowCellSampleNovaSeq6000Bcl2Fastq,
):
    """Test that adapting indexes of a sample that needs reverse complement but no padding works."""
    # GIVEN a run parameters file that needs reverse complement of indexes
    assert is_reverse_complement(run_parameters=novaseq_6000_run_parameters)
    # GIVEN a sample that does not need padding
    assert (
        novaseq_6000_run_parameters.get_index_1_cycles() == LONG_INDEX_CYCLE_NR
        and len(novaseq6000_flow_cell_sample_before_adapt_indexes.index) >= 2 * LONG_INDEX_CYCLE_NR
    )
    samples: List = [novaseq6000_flow_cell_sample_before_adapt_indexes]
    initial_indexes: List[str] = novaseq6000_flow_cell_sample_before_adapt_indexes.index.split("-")
    initial_index1: str = initial_indexes[0]
    initial_index2: str = initial_indexes[1]

    # WHEN adapting the indexes of the sample
    adapt_indexes(samples=samples, run_parameters=novaseq_6000_run_parameters)
    test_sample: FlowCellSampleNovaSeq6000Bcl2Fastq = samples[0]

    # THEN the first index was correctly adapted
    assert len(test_sample.index) == LONG_INDEX_CYCLE_NR
    assert test_sample.index == initial_index1
    # THEN the second index was correctly adapted
    assert len(test_sample.index2) == LONG_INDEX_CYCLE_NR
    assert test_sample.index2 == get_reverse_complement_dna_seq(dna=initial_index2)


def test_adapt_indexes_no_reverse_complement_no_padding(
    novaseq_x_run_parameters: RunParameters,
    novaseq_x_flow_cell_sample_before_adapt_indexes: FlowCellSampleNovaSeqX,
):
    """Test that adapting indexes of a sample that does not need reverse complement nor padding works."""
    # GIVEN a run parameters file that does not need reverse complement of indexes
    assert not is_reverse_complement(run_parameters=novaseq_x_run_parameters)
    # GIVEN a sample that does not need padding
    assert (
        novaseq_x_run_parameters.get_index_1_cycles() == LONG_INDEX_CYCLE_NR
        and len(novaseq_x_flow_cell_sample_before_adapt_indexes.index) >= 2 * LONG_INDEX_CYCLE_NR
    )
    samples: List = [novaseq_x_flow_cell_sample_before_adapt_indexes]
    initial_indexes: List[str] = novaseq_x_flow_cell_sample_before_adapt_indexes.index.split("-")
    initial_index1: str = initial_indexes[0]
    initial_index2: str = initial_indexes[1]

    # WHEN adapting the indexes of the sample
    adapt_indexes(samples=samples, run_parameters=novaseq_x_run_parameters)
    test_sample: FlowCellSampleNovaSeq6000Bcl2Fastq = samples[0]

    # THEN the first index was correctly adapted
    assert len(test_sample.index) == LONG_INDEX_CYCLE_NR
    assert test_sample.index == initial_index1
    # THEN the second index was correctly adapted
    assert len(test_sample.index2) == LONG_INDEX_CYCLE_NR
    assert test_sample.index2 == initial_index2
