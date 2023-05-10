""" Create a sample sheet for Novaseq flow cells."""

import logging
from typing import Dict, List, Set

from cg.apps.demultiplex.sample_sheet import index
from cg.apps.demultiplex.sample_sheet.dummy_sample import dummy_sample
from cg.apps.demultiplex.sample_sheet.index import Index
from cg.apps.demultiplex.sample_sheet.validate import get_sample_sheet
from cg.apps.lims.samplesheet import LimsFlowcellSample
from cg.constants.demultiplexing import (
    SAMPLE_SHEET_DATA_HEADER,
    SAMPLE_SHEET_HEADERS,
    SAMPLE_SHEET_SETTINGS_HEADER,
    SAMPLE_SHEET_SETTING_BARCODE_MISMATCH_INDEX1,
    SAMPLE_SHEET_SETTING_BARCODE_MISMATCH_INDEX2,
)
from cg.models.demultiplex.run_parameters import RunParameters

LOG = logging.getLogger(__name__)


class SampleSheetCreator:
    """Create a raw sample sheet for Novaseq flow cells."""

    def __init__(
        self,
        bcl_converter: str,
        flowcell_id: str,
        lims_samples: List[LimsFlowcellSample],
        run_parameters: RunParameters,
        force: bool = False,
    ):
        self.bcl_converter = bcl_converter
        self.flowcell_id: str = flowcell_id
        self.lims_samples: List[LimsFlowcellSample] = lims_samples
        self.run_parameters: RunParameters = run_parameters
        self.force = force

    @property
    def valid_indexes(self) -> List[Index]:
        return index.get_valid_indexes(dual_indexes_only=True)

    def add_dummy_samples(self) -> None:
        """Add all dummy samples with non-existing indexes to samples

        dummy samples are added if there are indexes that are not used by the actual samples.
        This means that we will add each dummy sample (that is needed) to each lane
        """
        LOG.info("Adding dummy samples for unused indexes")
        indexes_by_lane: Dict[int, Set[str]] = index.get_indexes_by_lane(samples=self.lims_samples)
        for lane, lane_indexes in indexes_by_lane.items():
            LOG.debug(f"Add dummy samples for lane {lane}")
            for index_obj in self.valid_indexes:
                if index.index_exists(index=index_obj.sequence, indexes=lane_indexes):
                    LOG.debug(f"Index {index_obj.sequence} already in use")
                    continue
                dummy_sample_obj: LimsFlowcellSample = dummy_sample(
                    flowcell=self.flowcell_id,
                    dummy_index=index_obj.sequence,
                    lane=lane,
                    name=index_obj.name,
                    bcl_converter=self.bcl_converter,
                )
                LOG.debug(f"Adding dummy sample {dummy_sample_obj} to lane {lane}")
                self.lims_samples.append(dummy_sample_obj)

    def remove_unwanted_samples(self) -> None:
        """Filter out samples with indexes of unwanted length and single indexes"""
        LOG.info("Removing all samples without dual indexes")
        samples_to_keep = []
        sample: LimsFlowcellSample
        for sample in self.lims_samples:
            if not index.is_dual_index(sample.index):
                LOG.warning(f"Removing sample {sample} since it does not have dual index")
                continue
            samples_to_keep.append(sample)
        self.lims_samples = samples_to_keep

    @staticmethod
    def convert_sample_to_header_dict(
        sample: LimsFlowcellSample,
        sample_sheet_headers: List[str],
    ) -> List[str]:
        """Convert a lims sample object to a dict with keys that corresponds to the sample sheet
        headers"""
        LOG.debug(f"Use sample sheet header {sample_sheet_headers}")
        sample_dict = sample.dict(by_alias=True)
        return [str(sample_dict[header]) for header in sample_sheet_headers]

    def convert_to_sample_sheet(self) -> List[List[str]]:
        """Create sample sheet with samples."""
        LOG.info("Create sample sheet for samples")
        sample_sheet: List[List[str]] = [
            [SAMPLE_SHEET_SETTINGS_HEADER],
            SAMPLE_SHEET_SETTING_BARCODE_MISMATCH_INDEX1,
            SAMPLE_SHEET_SETTING_BARCODE_MISMATCH_INDEX2,
            [SAMPLE_SHEET_DATA_HEADER],
            SAMPLE_SHEET_HEADERS[self.bcl_converter],
        ]
        for sample in self.lims_samples:
            sample_sheet.append(
                self.convert_sample_to_header_dict(
                    sample=sample,
                    sample_sheet_headers=SAMPLE_SHEET_HEADERS[self.bcl_converter],
                )
            )
        return sample_sheet

    def construct_sample_sheet(self) -> List[List[str]]:
        """Construct the sample sheet"""
        LOG.info(f"Constructing sample sheet for {self.flowcell_id}")
        # Create dummy samples for the indexes that is missing
        if self.run_parameters.requires_dummy_samples:
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
        sample_sheet: List[List[str]] = self.convert_to_sample_sheet()
        if self.force:
            LOG.info("Skipping validation of sample sheet due to force flag")
            return sample_sheet
        LOG.info("Validating sample sheet")
        get_sample_sheet(
            sample_sheet_content=sample_sheet,
            flow_cell_mode="S2",
            bcl_converter=self.bcl_converter,
        )
        LOG.info("Sample sheet looks fine")
        return sample_sheet
