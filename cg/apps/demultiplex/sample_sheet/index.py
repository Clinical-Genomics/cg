"""Functions that deal with modifications of the indexes."""
import logging
from typing import Union

from packaging import version
from pydantic import BaseModel

from cg.apps.demultiplex.sample_sheet.models import (
    FlowCellSample,
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.constants.constants import FileFormat
from cg.constants.sequencing import Sequencers
from cg.io.controller import ReadFile
from cg.models.demultiplex.run_parameters import RunParameters
from cg.resources import VALID_INDEXES_PATH
from cg.utils.utils import get_hamming_distance

LOG = logging.getLogger(__name__)
DNA_COMPLEMENTS: dict[str, str] = {"A": "T", "C": "G", "G": "C", "T": "A"}
INDEX_ONE_PAD_SEQUENCE: str = "AT"
INDEX_TWO_PAD_SEQUENCE: str = "AC"
LONG_INDEX_CYCLE_NR: int = 10
MINIMUM_HAMMING_DISTANCE: int = 3
NEW_CONTROL_SOFTWARE_VERSION: str = "1.7.0"
NEW_REAGENT_KIT_VERSION: str = "1.5"
REAGENT_KIT_PARAMETER_TO_VERSION: dict[str, str] = {"1": "1.0", "3": "1.5"}
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


def get_reagent_kit_version(reagent_kit_version: str) -> str:
    """Derives the reagent kit version from the run parameters."""
    LOG.info(f"Converting reagent kit parameter {reagent_kit_version} to version")
    if reagent_kit_version not in REAGENT_KIT_PARAMETER_TO_VERSION:
        raise SyntaxError(f"Unknown reagent kit version {reagent_kit_version}")

    return REAGENT_KIT_PARAMETER_TO_VERSION[reagent_kit_version]


def get_index_pair(sample: FlowCellSample) -> tuple[str, str]:
    """Returns a sample index separated into index 1 and index 2."""
    if is_dual_index(sample.index):
        index_1, index_2 = sample.index.split("-")
        return index_1.strip(), index_2.strip()
    return sample.index, sample.index2


def is_reverse_complement_needed(run_parameters: RunParameters) -> bool:
    """Return True if the second index requires reverse complement.

    If the run used the new NovaSeq control software version (NEW_CONTROL_SOFTWARE_VERSION)
    and the new reagent kit version (NEW_REAGENT_KIT_VERSION), then it requires reverse complement.
    If the run is NovaSeqX, does not require reverse complement.
    """
    if run_parameters.sequencer == Sequencers.NOVASEQX:
        return False
    control_software_version: str = run_parameters.control_software_version
    reagent_kit_version: str = run_parameters.reagent_kit_version
    LOG.info("Check if run is reverse complement")
    if version.parse(version=control_software_version) < version.parse(
        version=NEW_CONTROL_SOFTWARE_VERSION
    ):
        LOG.warning(
            f"Old software version {control_software_version}, no need for reverse complement"
        )
        return False
    reagent_kit_version: str = get_reagent_kit_version(reagent_kit_version=reagent_kit_version)
    if version.parse(reagent_kit_version) < version.parse(NEW_REAGENT_KIT_VERSION):
        LOG.warning(
            f"Reagent kit version {reagent_kit_version} does not does not need reverse complement"
        )
        return False
    LOG.info("Run is reverse complement")
    return True


def is_padding_needed(index_cycles: int, sample_index_length: int) -> bool:
    """Returns whether a sample needs padding or not given the sample index length.
    A sample needs padding if its adapted index length is shorter than the number of index cycles
    reads stated in the run parameters file of the sequencing. This happens when the sample index
    is 8 nucleotides long and the number of index cycles read is 10 nucleotides.
    """
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
    """Get the hamming distance between two index 1 sequences.
    In the case that one sequence is longer than the other, the distance is calculated between
    the shortest sequence and the first segment of equal length of the longest sequence."""
    shortest_index_length: int = min(len(sequence_1), len(sequence_2))
    return get_hamming_distance(
        str_1=sequence_1[:shortest_index_length], str_2=sequence_2[:shortest_index_length]
    )


def get_hamming_distance_index_2(
    sequence_1: str, sequence_2: str, is_reverse_complement: bool
) -> int:
    """Get the hamming distance between two index 2 sequences.
    In the case that one sequence is longer than the other, the distance is calculated between
    the shortest sequence and the last segment of equal length of the longest sequence.
    If the sample requires reverse complement, the calculation is the same as for index 1."""
    shortest_index_length: int = min(len(sequence_1), len(sequence_2))
    return (
        get_hamming_distance(
            str_1=sequence_1[:shortest_index_length], str_2=sequence_2[:shortest_index_length]
        )
        if is_reverse_complement
        else get_hamming_distance(
            str_1=sequence_1[-shortest_index_length:], str_2=sequence_2[-shortest_index_length:]
        )
    )


def update_barcode_mismatch_values_for_sample(
    sample_to_update: FlowCellSampleBCLConvert,
    samples_to_compare_to: list[FlowCellSampleBCLConvert],
    is_reverse_complement: bool,
) -> None:
    """Updates the sample's barcode mismatch values.
    If a sample index has a hamming distance to any other sample lower than the threshold
    (3 nucleotides), the barcode mismatch value for that index is set to zero."""
    index_1_sample_to_update, index_2_sample_to_update = get_index_pair(sample=sample_to_update)
    for sample_to_compare_to in samples_to_compare_to:
        if sample_to_update.sample_id == sample_to_compare_to.sample_id:
            continue
        index_1, index_2 = get_index_pair(sample=sample_to_compare_to)
        if (
            get_hamming_distance_index_1(sequence_1=index_1_sample_to_update, sequence_2=index_1)
            < MINIMUM_HAMMING_DISTANCE
        ):
            LOG.debug(
                f"Turning barcode mismatch for index 1 to 0 for sample {sample_to_update.sample_id}"
            )
            sample_to_update.barcode_mismatches_1 = 0
        if (
            get_hamming_distance_index_2(
                sequence_1=index_2_sample_to_update,
                sequence_2=index_2,
                is_reverse_complement=is_reverse_complement,
            )
            < MINIMUM_HAMMING_DISTANCE
        ):
            LOG.debug(
                f"Turning barcode mismatch for index 2 to 0 for sample {sample_to_update.sample_id}"
            )
            sample_to_update.barcode_mismatches_2 = 0


def pad_and_reverse_complement_sample_indexes(
    sample: FlowCellSample, index_cycles: int, is_reverse_complement: bool
) -> None:
    """Adapts the indexes of sample.
    1. Pad indexes if needed so that all indexes have a length equal to the number of index reads
    2. Takes the reverse complement of index 2 in case of the new NovaSeq software control version
    (1.7) in combination with the new reagent kit (version 1.5).
    3. Assigns the indexes to the sample attributes index and index2."""
    index1, index2 = get_index_pair(sample=sample)
    index_length = len(index1)
    if isinstance(sample, FlowCellSampleBcl2Fastq) and is_padding_needed(
        index_cycles=index_cycles, sample_index_length=index_length
    ):
        LOG.debug("Padding indexes")
        index1 = pad_index_one(index_string=index1)
        index2 = pad_index_two(index_string=index2, reverse_complement=is_reverse_complement)
    LOG.debug(f"Padding not necessary for sample {sample.sample_id}")
    if is_reverse_complement:
        index2 = get_reverse_complement_dna_seq(index2)
    sample.index = index1
    sample.index2 = index2


def update_indexes_for_samples(
    samples: list[Union[FlowCellSampleBCLConvert, FlowCellSampleBcl2Fastq]],
    index_cycles: int,
    is_reverse_complement: bool,
) -> None:
    """Updates the values to the fields index1 and index 2 of samples."""
    for sample in samples:
        pad_and_reverse_complement_sample_indexes(
            sample=sample,
            index_cycles=index_cycles,
            is_reverse_complement=is_reverse_complement,
        )
