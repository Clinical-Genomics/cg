""" Create a samplesheet for Novaseq flowcells """

import csv
from pathlib import Path
from typing import Dict, List, Set

from cg.apps.lims.samplesheet import LimsFlowcellSample
from cg.models.demultiplex import valid_indexes
from cg.models.demultiplex.run_parameters import RunParameters
from cg.models.demultiplex.valid_indexes import Index
from cg.resources import valid_indexes_path


class NovaseqSampleSheet:
    """ Create a raw sample sheet for Novaseq flowcells """

    NEW_CONTROL_SOFTWARE_VERSION = "1.7.0"
    NEW_REAGENT_KIT_VERSION = 1.5
    HEADER_TO_LIMS_KEY = {
        "FCID": "flowcell_id",
        "Lane": "lane",
        "SampleID": "sample_id",
        "SampleRef": "sample_ref",
        "index": "index",
        "index2": "index2",
        "SampleName": "sample_name",
        "Control": "control",
        "Recipe": "recipe",
        "Operator": "operator",
        "Project": "project",
    }
    SAMPLE_SHEET_HEADERS = [
        "FCID",
        "Lane",
        "SampleID",
        "SampleRef",
        "index",
        "index2",
        "SampleName",
        "Control",
        "Recipe",
        "Operator",
        "Project",
    ]

    def __init__(
        self,
        flowcell: str,
        index_length: int,
        pad: bool,
        lims_samples: List[LimsFlowcellSample],
        dummy_indexes_file: Path,
        run_parameters: RunParameters,
    ):
        self.flowcell: str = flowcell
        self.index_length: int = index_length
        self.pad: bool = pad
        self.lims_samples: List[LimsFlowcellSample] = lims_samples
        self.dummy_indexes_file: Path = dummy_indexes_file
        self.run_parameters: RunParameters = run_parameters
        self.valid_indexes: List[Index] = self.get_valid_indexes()

    @staticmethod
    def get_valid_indexes() -> List[Index]:
        with open(valid_indexes_path, "r") as csv_file:
            indexes_csv = csv.reader(csv_file)
            indexes: List[Index] = [Index(name=row[0], sequence=row[1]) for row in indexes_csv]
        return indexes

    @staticmethod
    def dummy_sample_name(sample_name: str) -> str:
        """Convert a string to a dummy sample name

        Replace space and parentheses with dashes
        """
        return sample_name.replace(" ", "-").replace("(", "-").replace(")", "-")

    @staticmethod
    def dummy_sample(flowcell: str, dummy_index: str, lane: int, name: str) -> LimsFlowcellSample:
        """ Constructs and returns a dummy sample in novaseq sample sheet format"""
        return LimsFlowcellSample(
            flowcell_id=flowcell,
            lane=lane,
            sample_id=NovaseqSampleSheet.dummy_sample_name(sample_name=name),
            index=dummy_index,
            sample_name="indexcheck",
            project="indexcheck",
        )

    @staticmethod
    def get_project_name(project: str) -> str:
        """ Only keeps the first part of the project name """
        return project.split()[0]

    @staticmethod
    def get_reverse_complement_dna_seq(dna: str) -> str:
        """ Generates the reverse complement of a DNA sequence"""
        complement = {"A": "T", "C": "G", "G": "C", "T": "A"}
        return "".join(complement[base] for base in reversed(dna))

    @staticmethod
    def is_dual_index(index: str) -> bool:
        """ Determines if an index in the raw sample sheet is dual index or not """
        return "-" in index

    @staticmethod
    def index_exists(index: str, indexes: Set[str]) -> bool:
        """ Determines if a index is already present in the existing indexes """
        return any(existing_index.startswith(index) for existing_index in indexes)

    def get_sample_indexes_in_lane(self, lane: int) -> Set[str]:
        """ Returns all sample indexes in a given lane """
        return {sample.index for sample in self.lims_samples if sample.lane == lane}

    def is_reverse_complement(self) -> bool:
        """If the run used the new NovaSeq control software version (NEW_CONTROL_SOFTWARE_VERSION)
        and the new reagent kit version (NEW_REAGENT_KIT_VERSION) the second index should be the
        reverse complement"""
        return (
            self.run_parameters.control_software_version == self.NEW_CONTROL_SOFTWARE_VERSION
            and self.get_reagent_kit_version(self.run_parameters.reagent_kit_version)
            == self.NEW_REAGENT_KIT_VERSION
        )

    def get_indexes_by_lane(self) -> Dict[int, Set[str]]:
        """Group the indexes by lane"""
        samples_by_lane = {}
        for sample in self.lims_samples:
            lane: int = sample.lane
            if lane not in samples_by_lane:
                samples_by_lane[lane] = set()
            samples_by_lane[lane].add(sample.index)
        return samples_by_lane

    def add_dummy_samples(self) -> None:
        """Add all dummy samples with non existing indexes to samples"""
        with open(f"{self.dummy_indexes_file}") as csv_file:
            dummy_samples_csv = csv.reader(csv_file, delimiter=COMMA)
            dummy_samples = [row for row in dummy_samples_csv]

        indexes_by_lane: Dict[int, Set[str]] = self.get_indexes_by_lane()
        for lane, indexes in indexes_by_lane.items():
            for index_obj in self.valid_indexes:
                if not self.index_exists(index=index_obj.sequence, indexes=indexes):
                    continue

                self.lims_samples.append(
                    self.dummy_sample(
                        flowcell=self.flowcell,
                        dummy_index=index_obj.sequence,
                        lane=lane,
                        name=index_obj.name,
                    )
                )

    def remove_unwanted_samples(self) -> None:
        """ Filter out samples with indexes of unwanted length and single indexes """
        self.lims_samples = [
            sample for sample in self.lims_samples if self.is_dual_index(sample.index)
        ]

    def adapt_indexes(self) -> None:
        """Adapts the indexes: pads all indexes so that all indexes have a length equal to the
        number  of index reads, and takes the reverse complement of index 2 in case of the new
        novaseq software control version (1.7) in combination with the new reagent kit
        (version 1.5)"""

        is_reverse_complement: bool = self.is_reverse_complement()

        for sample in self.lims_samples:
            index1, index2 = sample.index.split("-")
            if self.pad and len(index1) == 8:
                self.pad_and_rc_indexes(sample=sample, is_reverse_complement=is_reverse_complement)
            elif len(index2) == 10:
                if not is_reverse_complement:
                    sample.index2 = index2
                    continue
                sample.index2 = self.get_reverse_complement_dna_seq(index2)
            else:
                continue

    def pad_and_rc_indexes(self, sample: LimsFlowcellSample, is_reverse_complement: bool) -> None:
        """ Pads and reverse complements indexes """
        index1, index2 = sample.index.split("-")
        if self.run_parameters.index_reads == 8:
            if not is_reverse_complement:
                sample.index2 = index2
                return
            sample.index2 = self.get_reverse_complement_dna_seq(index2)

        if self.run_parameters.index_reads == 10:
            sample.index = index1 + "AT"
            if not is_reverse_complement:
                sample.index2 = index2 + "AC"
                return
            sample.index2 = self.get_reverse_complement_dna_seq("AC" + index2)

    @staticmethod
    def get_reagent_kit_version(reagent_kit_version: str) -> float:
        """ Derives the reagent kit version from the run parameters """

        parameter_to_version = {"1": 1.0, "3": 1.5}
        if reagent_kit_version not in parameter_to_version:
            raise SyntaxError(f"Unknown reagent kit version {reagent_kit_version}")

        return parameter_to_version[reagent_kit_version]

    def convert_sample_to_header_dict(self, sample: LimsFlowcellSample) -> List[str]:
        """Convert a lims sample object to a dict with keys that corresponds to the sample sheet headers"""
        sample_dict = sample.json()
        return [
            sample_dict[self.HEADER_TO_LIMS_KEY[header]] for header in self.SAMPLE_SHEET_HEADERS
        ]

    def convert_to_sample_sheet(self) -> str:
        """Convert all samples to a string with the sample sheet"""
        sample_sheet = [",".join(self.SAMPLE_SHEET_HEADERS)]
        for sample in self.lims_samples:
            sample_sheet.append(",".join(self.convert_sample_to_header_dict(sample=sample)))
        return "\n".join(sample_sheet)

    def construct_sample_sheet(self) -> str:
        """ Construct the sample sheet """
        # Create dummy samples for the indexes that is missing
        self.add_dummy_samples()
        self.remove_unwanted_samples()
        self.adapt_indexes()

        return self.convert_to_sample_sheet()
