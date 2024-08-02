import logging

from cg.constants.demultiplexing import SampleSheetBCLConvertSections
from cg.services.illumina.sample_sheet.models import IlluminaSampleIndexSetting
from cg.utils.utils import get_hamming_distance

LOG = logging.getLogger(__name__)
DNA_COMPLEMENTS: dict[str, str] = {"A": "T", "C": "G", "G": "C", "T": "A"}
MINIMUM_HAMMING_DISTANCE: int = 3


def find_line_containing_pattern(content: list[list[str]], pattern: str) -> int:
    """
    Find the line in the content that contains a pattern.
    Raises:
        ValueError: if the pattern is not found in the content.
    """
    for index, line in enumerate(content):
        if pattern in line:
            return index
    raise ValueError(f"Pattern {pattern} not found in content")


def is_dual_index(index: str) -> bool:
    """Determines if an index in the raw sample sheet is dual index or not."""
    return "-" in index


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


def get_samples_by_lane(
    samples: list[IlluminaSampleIndexSetting], lane: int
) -> list[IlluminaSampleIndexSetting]:
    """Return the samples of a given lane."""
    return [sample for sample in samples if sample.lane == lane]


def get_sample_column_names(
    is_run_single_index: bool, samples: list[IlluminaSampleIndexSetting]
) -> list[str]:
    """Return the column names of the sample sheet data section given the samples."""
    column_names: list[str] = SampleSheetBCLConvertSections.Data.column_names()
    if is_run_single_index:
        column_names.remove(SampleSheetBCLConvertSections.Data.BARCODE_MISMATCHES_2)
        column_names.remove(SampleSheetBCLConvertSections.Data.INDEX_2)
    if not all([sample.index for sample in samples]):
        column_names.remove(SampleSheetBCLConvertSections.Data.BARCODE_MISMATCHES_1)
    return column_names
