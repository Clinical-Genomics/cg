""" Create a samplesheet for Novaseq flowcells """

import logging
from typing import Dict, List, Set

from cg.apps.lims.samplesheet import LimsFlowcellSample
from cg.models.demultiplex.run_parameters import RunParameters
from cg.models.demultiplex.valid_indexes import Index
from cg.apps.demultiplex import index


LOG = logging.getLogger(__name__)


class SampleSheet:
    """ Create a raw sample sheet for Novaseq flowcells """

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
        lims_samples: List[LimsFlowcellSample],
        run_parameters: RunParameters,
        index_length: int = 8,
        pad: bool = False,
    ):
        self.flowcell: str = flowcell
        self.index_length: int = index_length
        self.pad: bool = pad
        self.lims_samples: List[LimsFlowcellSample] = lims_samples
        self.run_parameters: RunParameters = run_parameters
        self.valid_indexes: List[Index] = index.get_valid_indexes()

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
            sample_id=SampleSheet.dummy_sample_name(sample_name=name),
            index=dummy_index,
            sample_name="indexcheck",
            project="indexcheck",
        )

    @staticmethod
    def get_project_name(project: str) -> str:
        """ Only keeps the first part of the project name """
        return project.split()[0]

    @staticmethod
    def index_exists(index: str, indexes: Set[str]) -> bool:
        """ Determines if a index is already present in the existing indexes """
        return any(existing_index.startswith(index) for existing_index in indexes)

    def get_sample_indexes_in_lane(self, lane: int) -> Set[str]:
        """ Returns all sample indexes in a given lane """
        return {sample.index for sample in self.lims_samples if sample.lane == lane}

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
        LOG.info("Removing all samples with dual indexes")
        samples_to_keep = []
        sample: LimsFlowcellSample
        for sample in self.lims_samples:
            if index.is_dual_index(sample.index):
                LOG.warning("Removing sample %s", sample.sample_id)
                continue
            samples_to_keep.append(sample)
        self.lims_samples = samples_to_keep

    @staticmethod
    def convert_sample_to_header_dict(
        sample: LimsFlowcellSample, sample_sheet_headers: List[str], header_to_lims: Dict[str, str]
    ) -> List[str]:
        """Convert a lims sample object to a dict with keys that corresponds to the sample sheet headers"""
        LOG.info("Use sample sheet header %s", sample_sheet_headers)
        print(sample_sheet_headers)
        print(header_to_lims)
        print(sample)
        sample_dict = sample.dict()
        return [str(sample_dict[header_to_lims[header]]) for header in sample_sheet_headers]

    def convert_to_sample_sheet(self) -> str:
        """Convert all samples to a string with the sample sheet"""
        sample_sheet = [",".join(self.SAMPLE_SHEET_HEADERS)]
        for sample in self.lims_samples:
            sample_sheet.append(
                ",".join(
                    self.convert_sample_to_header_dict(
                        sample=sample,
                        sample_sheet_headers=self.SAMPLE_SHEET_HEADERS,
                        header_to_lims=self.HEADER_TO_LIMS_KEY,
                    )
                )
            )
        return "\n".join(sample_sheet)

    def construct_sample_sheet(self) -> str:
        """ Construct the sample sheet """
        # Create dummy samples for the indexes that is missing
        self.add_dummy_samples()
        self.remove_unwanted_samples()
        self.adapt_indexes()

        return self.convert_to_sample_sheet()
