""" Create a sample sheet for Novaseq flow cells."""

import logging
from typing import Dict, List, Set

from cg.apps.demultiplex.sample_sheet import index
from cg.apps.demultiplex.sample_sheet.dummy_sample import dummy_sample
from cg.apps.demultiplex.sample_sheet.index import Index
from cg.apps.demultiplex.sample_sheet.validate import validate_sample_sheet
from cg.apps.demultiplex.sample_sheet.models import FlowCellSample
from cg.constants.demultiplexing import (
    SAMPLE_SHEET_HEADERS,
    SAMPLE_SHEET_SETTINGS_HEADER,
    SAMPLE_SHEET_SETTING_BARCODE_MISMATCH_INDEX1,
    SAMPLE_SHEET_SETTING_BARCODE_MISMATCH_INDEX2,
    SampleSheetHeaderColumnNames,
)
from cg.models.demultiplex.flow_cell import FlowCell
from cg.models.demultiplex.run_parameters import RunParameters

LOG = logging.getLogger(__name__)


class SampleSheetCreator:
    """Create a raw sample sheet for Novaseq flow cells."""

    def __init__(
        self,
        bcl_converter: str,
        flow_cell: FlowCell,
        lims_samples: List[FlowCellSample],
        force: bool = False,
    ):
        self.bcl_converter = bcl_converter
        self.flow_cell_id: str = flow_cell.id
        self.lims_samples: List[FlowCellSample] = lims_samples
        self.run_parameters: RunParameters = flow_cell.run_parameters
        self.force = force

    @property
    def valid_indexes(self) -> List[Index]:
        return index.get_valid_indexes(dual_indexes_only=True)

    def add_dummy_samples(self) -> None:
        """Add all dummy samples with non-existing indexes to samples.

        Dummy samples are added if there are indexes that are not used by the actual samples.
        This means that we will add each dummy sample (that is needed) to each lane.
        """
        LOG.info("Adding dummy samples for unused indexes")
        indexes_by_lane: Dict[int, Set[str]] = index.get_indexes_by_lane(samples=self.lims_samples)
        for lane, lane_indexes in indexes_by_lane.items():
            LOG.debug(f"Add dummy samples for lane {lane}")
            for index_obj in self.valid_indexes:
                if index.index_exists(index=index_obj.sequence, indexes=lane_indexes):
                    LOG.debug(f"Index {index_obj.sequence} already in use")
                    continue
                dummy_flow_cell_sample: FlowCellSample = dummy_sample(
                    flow_cell_id=self.flow_cell_id,
                    dummy_index=index_obj.sequence,
                    lane=lane,
                    name=index_obj.name,
                    bcl_converter=self.bcl_converter,
                )
                LOG.debug(f"Adding dummy sample {dummy_flow_cell_sample} to lane {lane}")
                self.lims_samples.append(dummy_flow_cell_sample)

    def remove_unwanted_samples(self) -> None:
        """Filter out samples with indexes of unwanted length and single indexes."""
        LOG.info("Removing all samples without dual indexes")
        samples_to_keep = []
        sample: FlowCellSample
        for sample in self.lims_samples:
            if not index.is_dual_index(sample.index):
                LOG.warning(f"Removing sample {sample} since it does not have dual index")
                continue
            samples_to_keep.append(sample)
        self.lims_samples = samples_to_keep

    @staticmethod
    def convert_sample_to_header_dict(
        sample: FlowCellSample,
        sample_sheet_headers: List[str],
    ) -> List[str]:
        """Convert a lims sample object to a dict with keys that corresponds to the sample sheet
        headers."""
        LOG.debug(f"Use sample sheet header {sample_sheet_headers}")
        sample_dict = sample.dict(by_alias=True)
        return [str(sample_dict[header]) for header in sample_sheet_headers]

    def create_sample_sheet_content(self) -> List[List[str]]:
        """Create sample sheet with samples."""
        LOG.info("Create sample sheet for samples")
        sample_sheet_content: List[List[str]] = [
            [SAMPLE_SHEET_SETTINGS_HEADER],
            SAMPLE_SHEET_SETTING_BARCODE_MISMATCH_INDEX1,
            SAMPLE_SHEET_SETTING_BARCODE_MISMATCH_INDEX2,
            [SampleSheetHeaderColumnNames.DATA],
            SAMPLE_SHEET_HEADERS[self.bcl_converter],
        ]
        for sample in self.lims_samples:
            sample_sheet_content.append(
                self.convert_sample_to_header_dict(
                    sample=sample,
                    sample_sheet_headers=SAMPLE_SHEET_HEADERS[self.bcl_converter],
                )
            )
        return sample_sheet_content

    def construct_sample_sheet(self) -> List[List[str]]:
        """Construct the sample sheet."""
        LOG.info(f"Constructing sample sheet for {self.flow_cell_id}")
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
        sample_sheet_content: List[List[str]] = self.create_sample_sheet_content()
        if self.force:
            LOG.info("Skipping validation of sample sheet due to force flag")
            return sample_sheet_content
        LOG.info("Validating sample sheet")
        validate_sample_sheet(
            sample_sheet_content=sample_sheet_content,
            bcl_converter=self.bcl_converter,
        )
        LOG.info("Sample sheet passed validation")
        return sample_sheet_content
