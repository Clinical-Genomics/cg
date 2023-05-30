""" Create a sample sheet for Novaseq flow cells."""
import logging
from typing import List

from cg.apps.demultiplex.sample_sheet import index
from cg.apps.demultiplex.sample_sheet.index import Index
from cg.apps.demultiplex.sample_sheet.validate import validate_sample_sheet
from cg.apps.demultiplex.sample_sheet.models import FlowCellSample
from cg.constants.demultiplexing import (
    BclConverter,
    SampleSheetSections,
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
        if bcl_converter == BclConverter.BCL2FASTQ:
            raise SampleSheetError(f"Can't use {BclConverter.BCL2FASTQ} with sample sheet v2")
        self.bcl_converter: str = BclConverter.DRAGEN
        self.flow_cell_id: str = flow_cell.id
        self.sequencer: str = flow_cell.sequencer_type
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

    def get_additional_sections_sample_sheet(self) -> List[List[str]]:
        """Build all sections of the sample sheet that is not the Data section."""
        header_section: List[List[str]] = [
            [SampleSheetSections.Header.HEADER],
            SampleSheetSections.Header.FILE_FORMAT,
            [SampleSheetSections.Header.RUN_NAME, self.flow_cell_id],
            [
                SampleSheetSections.Header.INSTRUMENT_PLATFORM,
                SampleSheetSections.INSTRUMENT_PLATFORMS[self.sequencer],
            ],
            SampleSheetSections.Header.INDEX_ORIENTATION_FORWARD,
        ]
        reads_section: List[List[str]] = [
            [SampleSheetSections.Reads.HEADER],
            [SampleSheetSections.Reads.READ_CYCLES_1, self.run_parameters.get_read1_cycles()],
            [SampleSheetSections.Reads.READ_CYCLES_2, self.run_parameters.get_read2_cycles()],
            [SampleSheetSections.Reads.INDEX_CYCLES_1, self.run_parameters.get_index1_cycles()],
            [SampleSheetSections.Reads.INDEX_CYCLES_2, self.run_parameters.get_index2_cycles()],
        ]
        settings_section: List[List[str]] = [
            [SampleSheetSections.Settings.HEADER],
            SampleSheetSections.Settings.SOFTWARE_VERSION,
            SampleSheetSections.Settings.FASTQ_COMPRESSION_FORMAT,
        ]
        return header_section + reads_section + settings_section

    def create_sample_sheet_content(self) -> List[List[str]]:
        """Create sample sheet with samples."""
        LOG.info("Create sample sheet for samples")
        sample_sheet_content: List[List[str]] = self.get_additional_sections_sample_sheet() + [
            [SampleSheetSections.Data.HEADER],
            SampleSheetSections.Data.COLUMN_NAMES,
        ]
        for sample in self.lims_samples:
            sample_sheet_content.append(
                self.convert_sample_to_header_dict(
                    sample=sample,
                    sample_sheet_headers=SampleSheetSections.Data.COLUMN_NAMES.value,
                )
            )
        return sample_sheet_content

    def construct_sample_sheet(self) -> List[List[str]]:
        """Construct the sample sheet."""
        LOG.info(f"Constructing sample sheet for {self.flow_cell_id}")
        self.remove_unwanted_samples()
        index.adapt_indexes(samples=self.lims_samples)
        self.add_override_cycles_to_samples()
        sample_sheet_content: List[List[str]] = self.create_sample_sheet_content()
        if self.force:
            LOG.info("Skipping validation of sample sheet due to force flag")
            return sample_sheet_content
        LOG.info("Validating sample sheet")
        validate_sample_sheet(
            sample_sheet_content=sample_sheet_content,
        )
        LOG.info("Sample sheet passed validation")
        return sample_sheet_content
