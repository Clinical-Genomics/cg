import logging

from cg.constants.demultiplexing import SampleSheetBcl2FastqSections
from cg.utils.utils import get_hamming_distance

LOG = logging.getLogger(__name__)
DNA_COMPLEMENTS: dict[str, str] = {"A": "T", "C": "G", "G": "C", "T": "A"}
MINIMUM_HAMMING_DISTANCE: int = 3


def get_reverse_complement_dna_seq(dna: str) -> str:
    """Generates the reverse complement of a DNA sequence."""
    LOG.debug(f"Reverse complementing string {dna}")

    return "".join(DNA_COMPLEMENTS[base] for base in reversed(dna))


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


def is_sample_sheet_bcl2fastq(content: list[list[str]]) -> bool:
    """Check if the sample sheet content corresponds to a Bcl2fastq sample sheet."""
    try:
        content.index([SampleSheetBcl2FastqSections.Data.HEADER])
        return True
    except ValueError:
        return False


def field_list_elements_validation(attribute: str, value: list[str], name: str) -> list[str]:
    """Validate that the list has two elements and the first element is the expected name."""
    if len(value) != 2:
        raise ValueError(f"{attribute} must have two entries.")
    elif value[0] != name:
        raise ValueError(f"The first entry of {attribute} must be '{name}'.")
    return value


def field_default_value_validation(
    attribute: str, value: list[str], default: list[str]
) -> list[str]:
    """Validate that the value is the default value."""
    if value != default:
        raise ValueError(f"{attribute} must be set to the default value: {default}")
    return value
