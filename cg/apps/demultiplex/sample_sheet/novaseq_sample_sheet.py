""" Create a samplesheet for Novaseq flowcells """

import logging
from typing import Dict, List, Set

from cg.apps.demultiplex.sample_sheet import index
from cg.apps.demultiplex.sample_sheet.dummy_sample import dummy_sample
from cg.apps.demultiplex.sample_sheet.index import Index
from cg.apps.lims.samplesheet import LimsFlowcellSample
from cg.models.demultiplex.run_parameters import RunParameters
from cgmodels.demultiplex.sample_sheet import get_sample_sheet

LOG = logging.getLogger(__name__)


class SampleSheetCreator:
    """Create a raw sample sheet for Novaseq flowcells"""

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
        flowcell_id: str,
        lims_samples: List[LimsFlowcellSample],
        run_parameters: RunParameters,
    ):
        self.flowcell_id: str = flowcell_id
        self.lims_samples: List[LimsFlowcellSample] = lims_samples
        self.run_parameters: RunParameters = run_parameters

    @property
    def valid_indexes(self) -> List[Index]:
        return index.get_valid_indexes(dual_indexes_only=True)

    @staticmethod
    def get_project_name(project: str) -> str:
        """Only keeps the first part of the project name"""
        return project.split()[0]

    def add_dummy_samples(self) -> None:
        """Add all dummy samples with non existing indexes to samples

        dummy samples are added if there are indexes that are not used by the actual samples.
        This means that we will add each dummy sample (that is needed) to each lane
        """
        LOG.info("Adding dummy samples for unused indexes")
        indexes_by_lane: Dict[int, Set[str]] = index.get_indexes_by_lane(samples=self.lims_samples)
        for lane, lane_indexes in indexes_by_lane.items():
            LOG.debug("Add dummy samples for lane %s", lane)
            for index_obj in self.valid_indexes:
                if index.index_exists(index=index_obj.sequence, indexes=lane_indexes):
                    LOG.debug("Index %s already in use", index_obj.sequence)
                    continue
                dummy_sample_obj: LimsFlowcellSample = dummy_sample(
                    flowcell=self.flowcell_id,
                    dummy_index=index_obj.sequence,
                    lane=lane,
                    name=index_obj.name,
                )
                LOG.debug("Adding dummy sample %s to lane %s", dummy_sample_obj, lane)
                self.lims_samples.append(dummy_sample_obj)

    def remove_unwanted_samples(self) -> None:
        """Filter out samples with indexes of unwanted length and single indexes"""
        LOG.info("Removing all samples without dual indexes")
        samples_to_keep = []
        sample: LimsFlowcellSample
        for sample in self.lims_samples:
            if not index.is_dual_index(sample.index):
                LOG.warning("Removing sample %s since it does not have dual index", sample)
                continue
            samples_to_keep.append(sample)
        self.lims_samples = samples_to_keep

    @staticmethod
    def convert_sample_to_header_dict(
        sample: LimsFlowcellSample, sample_sheet_headers: List[str], header_to_lims: Dict[str, str]
    ) -> List[str]:
        """Convert a lims sample object to a dict with keys that corresponds to the sample sheet headers"""
        LOG.debug("Use sample sheet header %s", sample_sheet_headers)
        sample_dict = sample.dict()
        return [str(sample_dict[header_to_lims[header]]) for header in sample_sheet_headers]

    def convert_to_sample_sheet(self) -> str:
        """Convert all samples to a string with the sample sheet"""
        LOG.info("Convert samples to string")
        sample_sheet = ["[Data]", ",".join(self.SAMPLE_SHEET_HEADERS)]
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
        """Construct the sample sheet"""
        LOG.info("Constructing sample sheet for %s", self.flowcell_id)
        # Create dummy samples for the indexes that is missing
        if self.run_parameters.run_type == "wgs":
            self.add_dummy_samples()
        else:
            LOG.info("Skip adding dummy samples since run is not WGS")
        self.remove_unwanted_samples()
        index.adapt_indexes(
            samples=self.lims_samples,
            control_software_version=self.run_parameters.control_software_version,
            reagent_kit_version=self.run_parameters.reagent_kit_version,
            expected_index_length=self.run_parameters.index_length,
        )
        sample_sheet: str = self.convert_to_sample_sheet()
        LOG.info("Validating sample sheet")
        get_sample_sheet(sample_sheet=sample_sheet, sheet_type="S2")
        LOG.info("Sample sheet looks fine")
        return sample_sheet
