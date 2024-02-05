"""Tests for functions related to indexes."""

import pytest

from cg.apps.demultiplex.sample_sheet.index import (
    Index,
    get_hamming_distance_index_1,
    get_hamming_distance_index_2,
    get_reverse_complement_dna_seq,
    get_valid_indexes,
    is_padding_needed,
)


def test_get_valid_indexes():
    """Test that the function get_valid_indexes returns a list of Index objects."""
    # GIVEN a sample sheet API

    # WHEN fetching the indexes
    indexes: list[Index] = get_valid_indexes()

    # THEN assert that the indexes are correct
    assert indexes
    assert isinstance(indexes[0], Index)


@pytest.mark.parametrize(
    "index1_cycles, index2_cycles, sample_index_length, expected_is_padding_needed",
    [
        (10, 10, 8, True),
        (10, 10, 10, False),
        (17, 8, 17, False),
        (8, 8, 10, False),
        (8, 8, 8, False),
    ],
)
def test_is_padding_needed(
    index1_cycles: int,
    index2_cycles: int,
    sample_index_length: int,
    expected_is_padding_needed: bool,
):
    """Test that evaluating if a situation needs padding returns the expected value."""
    # GIVEN a sample index length and the number of index cycles reads stated in the run parameters

    # WHEN checking if padding is needed
    padding_needed: bool = is_padding_needed(
        index1_cycles=index1_cycles,
        index2_cycles=index2_cycles,
        sample_index_length=sample_index_length,
    )

    # THEN assert that the result is the expected
    assert padding_needed == expected_is_padding_needed


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


@pytest.mark.parametrize(
    "sequence_1, sequence_2, expected_distance",
    [
        ("GATTACA", "GATTACA", 0),
        ("GATTACA", "GATTACAXX", 0),
        ("XXXACA", "GATTACA", 6),
        ("XXXXXXX", "GATTACA", 7),
    ],
    ids=[
        "Identical sequences",
        "Same initial part, different lengths",
        "Same final part, different lengths",
        "Different sequences, same length",
    ],
)
def test_get_hamming_distance_index_1(sequence_1: str, sequence_2: str, expected_distance: int):
    """
    Test that Hamming distances are calculated correctly for different sets of index 1 sequences.
    This is, that the operation is commutative and aligns sequences from the left.
    """
    # GIVEN two index_1 sequences

    # WHEN getting the hamming distance between them in any order

    # THEN the distance is zero
    assert (
        get_hamming_distance_index_1(sequence_1=sequence_1, sequence_2=sequence_2)
        == expected_distance
    )
    assert (
        get_hamming_distance_index_1(sequence_1=sequence_2, sequence_2=sequence_1)
        == expected_distance
    )


@pytest.mark.parametrize(
    "sequence_1, sequence_2, expected_distance",
    [
        ("GATTACA", "GATTACA", 0),
        ("GATTACA", "XXGATTACA", 0),
        ("GATXX", "GATTACA", 5),
        ("XXXXXXX", "GATTACA", 7),
    ],
    ids=[
        "Identical sequences",
        "Same final part, different lengths",
        "Same initial part, different lengths",
        "Different sequences, same length",
    ],
)
def test_get_hamming_distance_index_2_reverse_complement(
    sequence_1: str, sequence_2: str, expected_distance: int
):
    """
    Test that Hamming distances are calculated correctly for different sets of index 2 sequences
    with reverse complement. This is, that the operation is commutative and aligns sequences from
    the right.
    """
    # GIVEN two index_2 sequences

    # WHEN getting the hamming distance between them in any order

    # THEN the distance is zero
    assert (
        get_hamming_distance_index_2(
            sequence_1=sequence_1, sequence_2=sequence_2, is_reverse_complement=True
        )
        == expected_distance
    )
    assert (
        get_hamming_distance_index_2(
            sequence_1=sequence_2, sequence_2=sequence_1, is_reverse_complement=True
        )
        == expected_distance
    )


@pytest.mark.parametrize(
    "sequence_1, sequence_2, expected_distance",
    [
        ("GATTACA", "GATTACA", 0),
        ("GATTACA", "GATTACAXX", 0),
        ("XXXACA", "GATTACA", 6),
        ("XXXXXXX", "GATTACA", 7),
    ],
    ids=[
        "Identical sequences",
        "Same initial part, different lengths",
        "Same final part, different lengths",
        "Different sequences, same length",
    ],
)
def test_get_hamming_distance_index_2_no_reverse_complement(
    sequence_1: str, sequence_2: str, expected_distance: int
):
    """
    Test that Hamming distances are calculated correctly for different sets of index 2 sequences
    without reverse complement. This is, that the operation is commutative and aligns sequences
    from the left.
    """
    # GIVEN two index_2 sequences

    # WHEN getting the hamming distance between them in any order with reverse complement

    # THEN the distance is zero
    assert (
        get_hamming_distance_index_2(
            sequence_1=sequence_1, sequence_2=sequence_2, is_reverse_complement=False
        )
        == expected_distance
    )
    assert (
        get_hamming_distance_index_2(
            sequence_1=sequence_2, sequence_2=sequence_1, is_reverse_complement=False
        )
        == expected_distance
    )
