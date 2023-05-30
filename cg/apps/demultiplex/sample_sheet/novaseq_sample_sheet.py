""" Create a sample sheet for Novaseq flow cells."""
import logging
from typing import Dict, List, Set, Optional

from cg.apps.demultiplex.sample_sheet import index
from cg.apps.demultiplex.sample_sheet.dummy_sample import dummy_sample
from cg.apps.demultiplex.sample_sheet.index import Index
from cg.apps.demultiplex.sample_sheet.validate import validate_sample_sheet
from cg.apps.demultiplex.sample_sheet.models import FlowCellSample
from cg.constants.demultiplexing import (
    BclConverter,
    SampleSheetV1Sections,
    SampleSheetV2Sections,
)
from cg.exc import SampleSheetError
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
        self.bcl_converter: str = bcl_converter
        self.flow_cell_id: str = flow_cell.id
        self.lims_samples: List[FlowCellSample] = lims_samples
        self.run_parameters: RunParameters = flow_cell.run_parameters
        self.force: bool = force

    @property
    def valid_indexes(self) -> List[Index]:
        return index.get_valid_indexes(dual_indexes_only=True)

    def remove_unwanted_samples(self) -> None:
        """Filter out samples with single indexes."""
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
        """Convert a lims sample object to a list that corresponds to the sample sheet headers."""
        LOG.debug(f"Use sample sheet header {sample_sheet_headers}")
        sample_dict = sample.dict(by_alias=True)
        return [str(sample_dict[header]) for header in sample_sheet_headers]

    def add_dummy_samples(self) -> None:
        """Add all dummy samples with non-existing indexes to samples if applicable."""
        raise NotImplementedError("Impossible to add dummy samples in parent class")

    def add_override_cycles_to_samples(self) -> None:
        """Add override cycles attribute to samples if sample sheet is v2."""
        raise NotImplementedError("Impossible to add override cycles to samples from parent class")

    def get_additional_sections_sample_sheet(self) -> Optional[List]:
        """Build all sections of the sample sheet that are not the Data section."""
        raise NotImplementedError("Impossible to get sample sheet sections from parent class")

    def get_data_section_header_and_columns(self) -> Optional[List[List[str]]]:
        """Return the header and column names of the data section of the sample sheet."""
        raise NotImplementedError("Impossible to get sample sheet sections from parent class")

    def create_sample_sheet_content(self) -> List[List[str]]:
        """Create sample sheet with samples."""
        LOG.info("Create sample sheet for samples")
        sample_sheet_content: List[List[str]] = (
            self.get_additional_sections_sample_sheet() + self.get_data_section_header_and_columns()
        )
        for sample in self.lims_samples:
            sample_sheet_content.append(
                self.convert_sample_to_header_dict(
                    sample=sample,
                    sample_sheet_headers=self.get_data_section_header_and_columns()[1],
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
            run_parameters=self.run_parameters,
        )
        self.add_override_cycles_to_samples()
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


class SampleSheetCreatorV1(SampleSheetCreator):
    """Create a raw sample sheet (v1) for NovaSeq6000 flow cells."""

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

    def add_override_cycles_to_samples(self) -> None:
        """Return None for sample sheet v1."""
        return

    def get_additional_sections_sample_sheet(self) -> List:
        """Return empty list for sample sheet v1."""
        return []

    def get_data_section_header_and_columns(self) -> List[List[str]]:
        """Return the header and column names of the data section of the sample sheet."""
        return [
            [SampleSheetV1Sections.Data.HEADER],
            SampleSheetV1Sections.DATA_COLUMN_NAMES[self.bcl_converter],
        ]


class SampleSheetCreatorV2(SampleSheetCreator):
    """Create a raw sample sheet (v2) for NovaSeqX flow cells."""

    def __init__(
        self,
        bcl_converter: str,
        flow_cell: FlowCell,
        lims_samples: List[FlowCellSample],
        force: bool = False,
    ):
        super().__init__(bcl_converter, flow_cell, lims_samples, force)
        if bcl_converter == BclConverter.BCL2FASTQ:
            raise SampleSheetError(f"Can't use {BclConverter.BCL2FASTQ} with sample sheet v2")
        self.bcl_converter: str = BclConverter.DRAGEN

    def add_dummy_samples(self) -> None:
        """Return None for sample sheet v2."""
        return

    def add_override_cycles_to_samples(self) -> None:
        """Add override cycles attribute to samples."""
        flow_cell_index_len: int = self.run_parameters.index_length
        read1_str: str = "Y" + str(self.run_parameters.get_read1_cycles()) + ";"
        read2_str: str = "Y" + str(self.run_parameters.get_read2_cycles()) + ";"
        index1_str: str = "I" + str(self.run_parameters.get_index1_cycles()) + ";"
        index2_str: str = "I" + str(self.run_parameters.get_index2_cycles()) + ";"
        for sample in self.lims_samples:
            sample_index_len: int = len(sample.index)
            if sample_index_len != flow_cell_index_len:
                index1_str = (
                    "I"
                    + str(sample_index_len)
                    + "N"
                    + str(flow_cell_index_len - sample_index_len)
                    + ";"
                )
                index2_str = (
                    "N"
                    + str(flow_cell_index_len - sample_index_len)
                    + "I"
                    + str(sample_index_len)
                    + ";"
                )
            sample.override_cycles = read1_str + index1_str + index2_str + read2_str

    def get_data_section_header_and_columns(self) -> List[List[str]]:
        """Return the header and column names of the data section of the sample sheet."""
        return [[SampleSheetV2Sections.Data.HEADER], SampleSheetV2Sections.Data.COLUMN_NAMES]

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
