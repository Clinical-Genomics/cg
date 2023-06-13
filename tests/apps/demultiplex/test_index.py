"""Tests for functions related to indexes."""
from typing import Dict, List, Set

import pytest

from cg.apps.demultiplex.sample_sheet.index import (
    Index,
    get_valid_indexes,
    get_indexes_by_lane,
    get_reagent_kit_version,
    get_reverse_complement_dna_seq,
)
from cg.apps.demultiplex.sample_sheet.models import FlowCellSampleNovaSeq6000Bcl2Fastq


def test_get_valid_indexes():
    """Test that the function get_valid_indexes returns a list of Index objects."""
    # GIVEN a sample sheet api

    # WHEN fetching the indexes
    indexes: List[Index] = get_valid_indexes()

    # THEN assert that the indexes are correct
    assert len(indexes) > 0
    assert isinstance(indexes[0], Index)


def test_get_indexes_by_lane(
    novaseq_sample_1: FlowCellSampleNovaSeq6000Bcl2Fastq,
    novaseq_sample_2: FlowCellSampleNovaSeq6000Bcl2Fastq,
):
    """Test that getting indexes by lane groups indexes correctly."""
    # GIVEN two samples on different lanes
    assert novaseq_sample_1.lane != novaseq_sample_2.lane

    # WHEN getting indexes by lane
    indexes_by_lane: Dict[int, Set[str]] = get_indexes_by_lane(
        samples=[novaseq_sample_1, novaseq_sample_2]
    )

    # THEN the result dictionary has two entries
    assert len(indexes_by_lane.keys()) == 2
    assert len(indexes_by_lane.values()) == 2


def test_get_reagent_kit_version_non_existent_reagent(caplog):
    """Test that getting a non-existent reagent kit version fails."""
    # GIVEN a non-existent reagent kit version
    non_existent_reagent: str = "2"

    # WHEN getting the reagent kit version
    with pytest.raises(SyntaxError) as exc_info:
        reagent_kit_version: str = get_reagent_kit_version(reagent_kit_version=non_existent_reagent)
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
    reverse_output: str = get_reverse_complement_dna_seq(dna=dna_strain)

    # THEN the result is the expected
    assert reverse_output == reversed_complement


def test_get_reverse_complement_not_dna(caplog):
    """Test."""
    # GIVEN a non-DNA strain
    strain: str = "ACCUCTGU"

    # WHEN getting the reverse complement
    with pytest.raises(KeyError):
        # THEN the process fails due to not recognising the unknown nucleotide
        reverse_output: str = get_reverse_complement_dna_seq(dna=strain)
