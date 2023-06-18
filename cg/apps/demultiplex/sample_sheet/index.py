"""Functions that deal with modifications of the indexes."""
import logging
from typing import Dict, List, Set

from cg.apps.demultiplex.sample_sheet.models import FlowCellSample
from cg.constants.constants import FileFormat
from cg.constants.sequencing import Sequencers
from cg.io.controller import ReadFile
from cg.models.demultiplex.run_parameters import RunParameters
from cg.resources import VALID_INDEXES_PATH
from packaging import version
from pydantic import BaseModel

LOG = logging.getLogger(__name__)
DNA_COMPLEMENTS: Dict[str, str] = {"A": "T", "C": "G", "G": "C", "T": "A"}
INDEX_ONE_PAD_SEQUENCE: str = "AT"
INDEX_TWO_PAD_SEQUENCE: str = "AC"
LONG_INDEX_CYCLE_NR: int = 10
NEW_CONTROL_SOFTWARE_VERSION: str = "1.7.0"
NEW_REAGENT_KIT_VERSION: str = "1.5"
REAGENT_KIT_PARAMETER_TO_VERSION: Dict[str, str] = {"1": "1.0", "3": "1.5"}
SHORT_SAMPLE_INDEX_LENGTH: int = 8


def index_exists(index: str, indexes: Set[str]) -> bool:
    """Determines if an index is already present in the existing indexes."""
    return any(existing_index.startswith(index) for existing_index in indexes)


def get_indexes_by_lane(samples: List[FlowCellSample]) -> Dict[int, Set[str]]:
    """Group the indexes from samples by lane."""
    indexes_by_lane = {}
    for sample in samples:
        lane: int = sample.lane
        if lane not in indexes_by_lane:
            indexes_by_lane[lane] = set()
        indexes_by_lane[lane].add(sample.index)
    return indexes_by_lane


class Index(BaseModel):
    """Class that represents an index."""

    name: str
    sequence: str


def get_valid_indexes(dual_indexes_only: bool = True) -> List[Index]:
    """Return a list of valid indexes from the valid indexes file."""
    LOG.info(f"Fetch valid indexes from {VALID_INDEXES_PATH}")
    indexes: List[Index] = []
    indexes_csv: List[List[str]] = ReadFile.get_content_from_file(
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


def is_reverse_complement(run_parameters: RunParameters) -> bool:
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
    A sample needs padding if its index length is shorter than the number of index cycles reads
    stated in the run parameters file of the sequencing. This happens when the sample index is
    8 nucleotides long and the number of index cycles read is 10 nucleotides.
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


def adapt_indexes(
    samples: List[FlowCellSample],
    run_parameters: RunParameters,
) -> None:
    """Adapts the indexes: pads all indexes so that all indexes have a length equal to the
    number  of index reads, and takes the reverse complement of index 2 in case of the new
    novaseq software control version (1.7) in combination with the new reagent kit
    (version 1.5).
    """
    LOG.info("Fix so that all indexes are in the correct format")
    reverse_complement: bool = is_reverse_complement(run_parameters=run_parameters)
    for sample in samples:
        index1, index2 = sample.index.split("-")
        index1: str = index1.strip()
        index2: str = index2.strip()
        index_length = len(index1)
        if is_padding_needed(
            index_cycles=run_parameters.index_length, sample_index_length=index_length
        ):
            LOG.debug("Padding indexes")
            index1 = pad_index_one(index_string=index1)
            index2 = pad_index_two(index_string=index2, reverse_complement=reverse_complement)
        if reverse_complement:
            index2 = get_reverse_complement_dna_seq(index2)
        sample.index = index1
        sample.index2 = index2


def is_dual_index(index: str) -> bool:
    """Determines if an index in the raw sample sheet is dual index or not."""
    return "-" in index
