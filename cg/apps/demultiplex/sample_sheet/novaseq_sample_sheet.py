""" Create a sample sheet for Novaseq flow cells."""

import logging
from typing import Dict, List, Set, Union

from cg.apps.demultiplex.sample_sheet import index
from cg.apps.demultiplex.sample_sheet.dummy_sample import dummy_sample
from cg.apps.demultiplex.sample_sheet.index import Index
from cg.apps.demultiplex.sample_sheet.validate import validate_sample_sheet
from cg.apps.lims.samplesheet import LimsFlowcellSample
from cg.constants.demultiplexing import (
    SAMPLE_SHEET_HEADERS,
    SampleSheetHeaderColumnNames,
    SampleSheetV2Sections,
)
from cg.constants.sequencing import Sequencers
from cg.models.demultiplex.flow_cell import FlowCell
from cg.models.demultiplex.run_parameters import RunParameters

LOG = logging.getLogger(__name__)


class SampleSheetCreator:
    """Create a raw sample sheet for Novaseq flow cells."""

    def __init__(
        self,
        flow_cell: FlowCell,
        lims_samples: List[LimsFlowcellSample],
        force: bool = False,
    ):
        self.flow_cell_id: str = flow_cell.id
        self.lims_samples: List[LimsFlowcellSample] = lims_samples
        self.run_parameters: RunParameters = flow_cell.run_parameters
        self.flow_cell_mode: str = flow_cell.mode
        self.force = force

    @property
    def valid_indexes(self) -> List[Index]:
        return index.get_valid_indexes(dual_indexes_only=True)

    @property
    def data_columns(self) -> List[str]:
        """."""
        pass

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
                dummy_sample_obj: LimsFlowcellSample = dummy_sample(
                    flowcell=self.flow_cell_id,
                    dummy_index=index_obj.sequence,
                    lane=lane,
                    name=index_obj.name,
                    bcl_converter=self.bcl_converter,
                )
                LOG.debug(f"Adding dummy sample {dummy_sample_obj} to lane {lane}")
                self.lims_samples.append(dummy_sample_obj)

    def remove_unwanted_samples(self) -> None:
        """Filter out samples with indexes of unwanted length and single indexes."""
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
    def convert_sample_to_list(
        sample: LimsFlowcellSample,
        sample_sheet_headers: List[str],
    ) -> List[str]:
        """Convert a lims sample object to a list with that corresponds to the sample sheet headers."""
        LOG.debug(f"Use sample sheet header {sample_sheet_headers}")
        sample_dict = sample.dict(by_alias=True)
        return [str(sample_dict[header]) for header in sample_sheet_headers]

    def get_additional_sections_sample_sheet(self) -> List:
        """Build all sections of the sample sheet that is not the Data section."""
        return []

    def create_sample_sheet_content(self) -> List[List[str]]:
        """Create sample sheet with samples."""
        LOG.info("Create sample sheet for samples")
        sample_sheet_content: List[List[str]] = self.get_additional_sections_sample_sheet() + [
            [SampleSheetHeaderColumnNames.DATA],
            self.data_columns,
        ]
        for sample in self.lims_samples:
            sample_sheet_content.append(
                self.convert_sample_to_list(
                    sample=sample,
                    sample_sheet_headers=self.data_columns,
                )
            )
        return sample_sheet_content

    def construct_sample_sheet(self) -> List[List[str]]:
        """Construct the sample sheet."""
        LOG.info(f"Constructing sample sheet for {self.flow_cell_id}")
        # Create dummy samples for the indexes that is missing
        # TODO risk assessment of dummy sample addition
        if self.run_parameters.requires_dummy_samples:
            self.add_dummy_samples()
        else:
            LOG.info("Skip adding dummy samples since run is not WGS")
        self.remove_unwanted_samples()
        # TODO make this function receive a RunParameters object and flow cell sequencer
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
        # TODO make this function version specific
        validate_sample_sheet(
            sample_sheet_content=sample_sheet_content,
            flow_cell_mode=self.flow_cell_mode,
            bcl_converter=self.bcl_converter,
        )
        LOG.info("Sample sheet passed validation")
        return sample_sheet_content


class SampleSheetCreatorV1(SampleSheetCreator):
    """."""

    def __init__(
        self,
        flow_cell: FlowCell,
        lims_samples: List[LimsFlowcellSample],
        bcl_converter: str,
        force: bool = False,
    ):
        super().__init__(flow_cell, lims_samples, force)
        self.bcl_converter = bcl_converter

    @property
    def data_columns(self) -> List[str]:
        """."""
        return SAMPLE_SHEET_HEADERS[self.bcl_converter]


class SampleSheetCreatorV2(SampleSheetCreator):
    """."""

    @property
    def data_columns(self) -> List[str]:
        """."""
        return SAMPLE_SHEET_HEADERS[Sequencers.NOVASEQX]

    def get_additional_sections_sample_sheet(self) -> List[List[str]]:
        """Build all sections of the sample sheet that is not the Data section."""
        header_section: List[List[str]] = [
            [SampleSheetV2Sections.Header.HEADER],
            SampleSheetV2Sections.Header.FILE_FORMAT,
            [SampleSheetV2Sections.Header.RUN_NAME, self.flow_cell_id],
            SampleSheetV2Sections.Header.INSTRUMENT_TYPE,
            SampleSheetV2Sections.Header.INSTRUMENT_PLATFORM,
            SampleSheetV2Sections.Header.INDEX_ORIENTATION_FORWARD,
        ]
        reads_section: List[List[str]] = [
            [SampleSheetV2Sections.Reads.HEADER],
            [SampleSheetV2Sections.Reads.READ_CYCLES_1, self.run_parameters.get_read1_cycles()],
            [SampleSheetV2Sections.Reads.READ_CYCLES_2, self.run_parameters.get_read2_cycles()],
            [SampleSheetV2Sections.Reads.INDEX_CYCLES_1, self.run_parameters.get_index1_cycles()],
            [SampleSheetV2Sections.Reads.INDEX_CYCLES_2, self.run_parameters.get_index2_cycles()],
        ]
        settings_section: List[List[str]] = [
            [SampleSheetV2Sections.Settings.HEADER],
            SampleSheetV2Sections.Settings.SOFTWARE_VERSION,
            SampleSheetV2Sections.Settings.FASTQ_COMPRESSION_FORMAT,
        ]
        return header_section + reads_section + settings_section
