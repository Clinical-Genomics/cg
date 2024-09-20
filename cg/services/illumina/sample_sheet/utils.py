import logging

from cg.constants.demultiplexing import SampleSheetBcl2FastqSections
from cg.utils.utils import get_hamming_distance

LOG = logging.getLogger(__name__)
DNA_COMPLEMENTS: dict[str, str] = {"A": "T", "C": "G", "G": "C", "T": "A"}
MINIMUM_HAMMING_DISTANCE: int = 3


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


def get_reverse_complement_dna_seq(dna: str) -> str:
    """Generates the reverse complement of a DNA sequence."""
    LOG.debug(f"Reverse complement string {dna}")

    return "".join(DNA_COMPLEMENTS[base] for base in reversed(dna))


def is_sample_sheet_bcl2fastq(content: list[list[str]]) -> bool:
    """Check if the sample sheet content corresponds to a Bcl2fastq sample sheet."""
    try:
        content.index([SampleSheetBcl2FastqSections.Data.HEADER])
        return True
    except ValueError:
        return False
