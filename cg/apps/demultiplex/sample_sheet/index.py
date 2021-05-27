"""Functions that deals with modifications of the indexes"""
import csv
import logging
from typing import Dict, List, Set

from cg.apps.lims.samplesheet import LimsFlowcellSample
from cg.resources import valid_indexes_path
from packaging import version
from pydantic import BaseModel

LOG = logging.getLogger(__name__)
NEW_CONTROL_SOFTWARE_VERSION = "1.7.0"
NEW_REAGENT_KIT_VERSION = "1.5"
DNA_COMPLEMENTS = {"A": "T", "C": "G", "G": "C", "T": "A"}
REAGENT_KIT_PARAMETER_TO_VERSION = {"1": "1.0", "3": "1.5"}


def index_exists(index: str, indexes: Set[str]) -> bool:
    """Determines if a index is already present in the existing indexes"""
    return any(existing_index.startswith(index) for existing_index in indexes)


def get_indexes_by_lane(samples: List[LimsFlowcellSample]) -> Dict[int, Set[str]]:
    """Group the indexes from samples by lane"""
    indexes_by_lane = {}
    for sample in samples:
        lane: int = sample.lane
        if lane not in indexes_by_lane:
            indexes_by_lane[lane] = set()
        indexes_by_lane[lane].add(sample.index)
    return indexes_by_lane


class Index(BaseModel):
    name: str
    sequence: str


def get_valid_indexes(dual_indexes_only: bool = True) -> List[Index]:
    LOG.info("Fetch valid indexes from %s", valid_indexes_path)
    indexes: List[Index] = []
    with open(valid_indexes_path, "r") as csv_file:
        indexes_csv = csv.reader(csv_file)
        for row in indexes_csv:
            index_name = row[0]
            index_sequence = row[1]
            if dual_indexes_only and not is_dual_index(index_sequence):
                continue
            indexes.append(Index(name=index_name, sequence=index_sequence))
    return indexes


def get_reagent_kit_version(reagent_kit_version: str) -> str:
    """Derives the reagent kit version from the run parameters"""
    LOG.info("Converting reagent kit parameter %s to version", reagent_kit_version)
    if reagent_kit_version not in REAGENT_KIT_PARAMETER_TO_VERSION:
        raise SyntaxError(f"Unknown reagent kit version {reagent_kit_version}")

    return REAGENT_KIT_PARAMETER_TO_VERSION[reagent_kit_version]


def is_reverse_complement(control_software_version: str, reagent_kit_version_string: str) -> bool:
    """If the run used the new NovaSeq control software version (NEW_CONTROL_SOFTWARE_VERSION)
    and the new reagent kit version (NEW_REAGENT_KIT_VERSION) the second index should be the
    reverse complement
    """
    LOG.info("Check if run is reverse complement")
    if version.parse(control_software_version) < version.parse(NEW_CONTROL_SOFTWARE_VERSION):
        LOG.warning(
            "Old software version %s, no need for reverse complement", control_software_version
        )
        return False
    reagent_kit_version: str = get_reagent_kit_version(reagent_kit_version_string)
    if version.parse(reagent_kit_version) < version.parse(NEW_REAGENT_KIT_VERSION):
        LOG.warning(
            "Reagent kit version %s does not does not need reverse complement",
            reagent_kit_version,
        )
        return False
    LOG.info("Run is reverse complement")
    return True


def get_reverse_complement_dna_seq(dna: str) -> str:
    """Generates the reverse complement of a DNA sequence"""
    LOG.debug("Reverse complement string %s", dna)

    return "".join(DNA_COMPLEMENTS[base] for base in reversed(dna))


def pad_index_one(index_string: str) -> str:
    """Adds bases 'AT' to index one"""
    return index_string + "AT"


def pad_index_two(index_string: str, reverse_complement: bool) -> str:
    """Adds bases to index two depending on if it should be reverse complement or not"""
    if reverse_complement:
        return "AC" + index_string
    return index_string + "AC"


def adapt_indexes(
    samples: List[LimsFlowcellSample],
    control_software_version: str,
    reagent_kit_version: str,
    expected_index_length: int,
) -> None:
    """Adapts the indexes: pads all indexes so that all indexes have a length equal to the
    number  of index reads, and takes the reverse complement of index 2 in case of the new
    novaseq software control version (1.7) in combination with the new reagent kit
    (version 1.5)
    """
    LOG.info("Fix so that all indexes are on the correct format")
    reverse_complement: bool = is_reverse_complement(
        control_software_version=control_software_version,
        reagent_kit_version_string=reagent_kit_version,
    )
    for sample in samples:
        index1, index2 = sample.index.split("-")
        index_length = len(index1)
        if expected_index_length == 10 and index_length == 8:
            LOG.debug("Padding indexes")
            index1 = pad_index_one(index_string=index1)
            index2 = pad_index_two(index_string=index2, reverse_complement=reverse_complement)
        if reverse_complement:
            index2 = get_reverse_complement_dna_seq(index2)
        sample.index = index1
        sample.index2 = index2


def is_dual_index(index: str) -> bool:
    """Determines if an index in the raw sample sheet is dual index or not"""
    return "-" in index
