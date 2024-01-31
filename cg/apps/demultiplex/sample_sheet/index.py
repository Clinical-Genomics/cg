"""Functions that deal with modifications of the indexes."""

import logging

from pydantic import BaseModel

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.resources import VALID_INDEXES_PATH
from cg.utils.utils import get_hamming_distance

LOG = logging.getLogger(__name__)
DNA_COMPLEMENTS: dict[str, str] = {"A": "T", "C": "G", "G": "C", "T": "A"}
INDEX_ONE_PAD_SEQUENCE: str = "AT"
INDEX_TWO_PAD_SEQUENCE: str = "AC"
LONG_INDEX_CYCLE_NR: int = 10
MINIMUM_HAMMING_DISTANCE: int = 3
SHORT_SAMPLE_INDEX_LENGTH: int = 8


def is_dual_index(index: str) -> bool:
    """Determines if an index in the raw sample sheet is dual index or not."""
    return "-" in index


class Index(BaseModel):
    """Class that represents an index."""

    name: str
    sequence: str


def get_valid_indexes(dual_indexes_only: bool = True) -> list[Index]:
    """Return a list of valid indexes from the valid indexes file."""
    LOG.info(f"Fetch valid indexes from {VALID_INDEXES_PATH}")
    indexes: list[Index] = []
    indexes_csv: list[list[str]] = ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=VALID_INDEXES_PATH
    )
    for row in indexes_csv:
        index_name: str = row[0]
        index_sequence: str = row[1]
        if dual_indexes_only and not is_dual_index(index=index_sequence):
            continue
        indexes.append(Index(name=index_name, sequence=index_sequence))
    return indexes


def is_padding_needed(index1_cycles: int, index2_cycles: int, sample_index_length: int) -> bool:
    """Returns whether a sample needs padding or not given the sample index length.
    A sample from a NovaSeq6000 flow cell needs padding if its adapted index lengths are shorter
    than the number of index cycles reads stated in the run parameters file for both indexes.
    This happens when the sample index is 8 nucleotides long and the number of index cycles read is
    10 nucleotides long.
    """
    index_cycles: int | None = index1_cycles if index1_cycles == index2_cycles else None
    return index_cycles == LONG_INDEX_CYCLE_NR and sample_index_length == SHORT_SAMPLE_INDEX_LENGTH


def get_reverse_complement_dna_seq(dna: str) -> str:
    """Generates the reverse complement of a DNA sequence."""
    LOG.debug(f"Reverse complement string {dna}")

    return "".join(DNA_COMPLEMENTS[base] for base in reversed(dna))


def pad_index_one(index_string: str) -> str:
    """Adds bases 'AT' to index one."""
    return index_string + INDEX_ONE_PAD_SEQUENCE


def pad_index_two(index_string: str, reverse_complement: bool) -> str:
    """Adds bases to index two depending on if it should be reverse complement or not."""
    if reverse_complement:
        return INDEX_TWO_PAD_SEQUENCE + index_string
    return index_string + INDEX_TWO_PAD_SEQUENCE


def get_hamming_distance_index_1(sequence_1: str, sequence_2: str) -> int:
    """
    Get the hamming distance between two index 1 sequences.
    In the case that one sequence is longer than the other, the distance is calculated between
    the shortest sequence and the first segment of equal length of the longest sequence.
    """
    shortest_index_length: int = min(len(sequence_1), len(sequence_2))
    return get_hamming_distance(
        str_1=sequence_1[:shortest_index_length], str_2=sequence_2[:shortest_index_length]
    )


def get_hamming_distance_index_2(
    sequence_1: str, sequence_2: str, is_reverse_complement: bool
) -> int:
    """
    Get the hamming distance between two index 2 sequences.
    In the case that one sequence is longer than the other, the distance is calculated between
    the shortest sequence and the last segment of equal length of the longest sequence.
    If it does not require reverse complement, the calculation is the same as for index 1.
    """
    shortest_index_length: int = min(len(sequence_1), len(sequence_2))
    return (
        get_hamming_distance(
            str_1=sequence_1[-shortest_index_length:], str_2=sequence_2[-shortest_index_length:]
        )
        if is_reverse_complement
        else get_hamming_distance(
            str_1=sequence_1[:shortest_index_length], str_2=sequence_2[:shortest_index_length]
        )
    )
