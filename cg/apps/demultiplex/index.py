"""Functions that deals with modifications of the indexes"""
import csv
import logging
from typing import List

from cg.apps.lims.samplesheet import LimsFlowcellSample
from cg.models.demultiplex.valid_indexes import Index
from cg.resources import valid_indexes_path

LOG = logging.getLogger(__name__)
NEW_CONTROL_SOFTWARE_VERSION = "1.7.0"
NEW_REAGENT_KIT_VERSION = 1.5


def get_valid_indexes() -> List[Index]:
    LOG.info("Fetch indexes from %s", valid_indexes_path)
    with open(valid_indexes_path, "r") as csv_file:
        indexes_csv = csv.reader(csv_file)
        indexes: List[Index] = [Index(name=row[0], sequence=row[1]) for row in indexes_csv]
    return indexes


def get_reagent_kit_version(reagent_kit_version: str) -> float:
    """ Derives the reagent kit version from the run parameters """
    LOG.info("Converting reagent kit parameter %s to version", reagent_kit_version)
    parameter_to_version = {"1": 1.0, "3": 1.5}
    if reagent_kit_version not in parameter_to_version:
        raise SyntaxError(f"Unknown reagent kit version {reagent_kit_version}")

    return parameter_to_version[reagent_kit_version]


def is_reverse_complement(control_software_version: str, reagent_kit_version_string: str) -> bool:
    """If the run used the new NovaSeq control software version (NEW_CONTROL_SOFTWARE_VERSION)
    and the new reagent kit version (NEW_REAGENT_KIT_VERSION) the second index should be the
    reverse complement
    """
    LOG.info("Check if run is reverse complement")
    if control_software_version != NEW_CONTROL_SOFTWARE_VERSION:
        LOG.warning("Invalid control software version %s!", control_software_version)
        return False
    reagent_kit_version: float = get_reagent_kit_version(reagent_kit_version_string)
    if reagent_kit_version != NEW_REAGENT_KIT_VERSION:
        LOG.warning(
            "Reagent kit version %s does not match the valid version %s",
            reagent_kit_version,
            NEW_CONTROL_SOFTWARE_VERSION,
        )
        return False
    return True


def get_reverse_complement_dna_seq(dna: str) -> str:
    """ Generates the reverse complement of a DNA sequence"""
    complement = {"A": "T", "C": "G", "G": "C", "T": "A"}
    return "".join(complement[base] for base in reversed(dna))


def pad_and_rc_indexes(
    sample: LimsFlowcellSample, reverse_complement: bool, index_reads: int
) -> None:
    """ Pads and reverse complements indexes """
    index1, index2 = sample.index.split("-")
    if index_reads not in [8, 10]:
        message = f"Invalid index length {index_reads}"
        LOG.warning(message)
        raise SyntaxError(message)
    if index_reads == 8:
        if reverse_complement:
            sample.index2 = get_reverse_complement_dna_seq(index2)
            return
        sample.index2 = index2

    if index_reads == 10:
        sample.index = index1 + "AT"
        if reverse_complement:
            sample.index2 = get_reverse_complement_dna_seq("AC" + index2)
            return
        sample.index2 = index2 + "AC"


def adapt_indexes(
    samples: List[LimsFlowcellSample],
    control_software_version: str,
    reagent_kit_version: str,
    pad: bool,
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
        if pad and len(index1) == 8:
            self.pad_and_rc_indexes(sample=sample, is_reverse_complement=is_reverse_complement)
        elif len(index2) == 10:
            if not is_reverse_complement:
                sample.index2 = index2
                continue
            sample.index2 = get_reverse_complement_dna_seq(index2)
        else:
            continue


def is_dual_index(index: str) -> bool:
    """ Determines if an index in the raw sample sheet is dual index or not """
    return "-" in index
