"""Tests for functions related to indexes."""
import pytest

from cg.apps.demultiplex.sample_sheet.index import (
    Index,
    get_hamming_distance_for_indexes,
    get_reverse_complement_dna_seq,
    get_valid_indexes,
)


def test_get_valid_indexes():
    """Test that the function get_valid_indexes returns a list of Index objects."""
    # GIVEN a sample sheet API

    # WHEN fetching the indexes
    indexes: list[Index] = get_valid_indexes()

    # THEN assert that the indexes are correct
    assert indexes
    assert isinstance(indexes[0], Index)


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


def test_get_hamming_distance_index_1_different_lengths():
    """Test that hamming distance between indexes with same prefix but different lengths is zero."""
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


def test_get_hamming_distance_index_1_different_prefixes():
    """Test that hamming distance for index 1 counts different characters from the left."""
    # GIVEN two index_1 sequences with different lengths differing by two characters
    # when aligned to the left
    sequence_1: str = "GATXX"
    sequence_2: str = "GATTACA"

    # WHEN getting the hamming distance between them in any order

    # THEN the distance is equal to the number of different characters
    assert get_hamming_distance_for_indexes(sequence_1=sequence_1, sequence_2=sequence_2) == 2
    assert get_hamming_distance_for_indexes(sequence_1=sequence_2, sequence_2=sequence_1) == 2
