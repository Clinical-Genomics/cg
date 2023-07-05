""" Create a sample sheet for NovaSeq flow cells."""
import logging
from typing import Dict, List, Optional, Set, Type

from cg.apps.demultiplex.sample_sheet.index import (
    Index,
    adapt_samples,
    get_indexes_by_lane,
    get_valid_indexes,
    index_exists,
    is_dual_index,
    is_reverse_complement,
)
from cg.apps.demultiplex.sample_sheet.validate import get_samples_by_lane, validate_sample_sheet
from cg.apps.demultiplex.sample_sheet.models import FlowCellSample
from cg.constants.demultiplexing import (
    BclConverter,
    SampleSheetNovaSeq6000Sections,
    SampleSheetNovaSeqXSections,
)
from cg.exc import SampleSheetError
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from cg.models.demultiplex.run_parameters import RunParameters

LOG = logging.getLogger(__name__)


class SampleSheetCreator:
    """Base class for sample sheet creation."""

    def __init__(
        self,
        bcl_converter: str,
        flow_cell: FlowCellDirectoryData,
        lims_samples: List[FlowCellSample],
        force: bool = False,
    ):
        self.bcl_converter: str = bcl_converter
        self.flow_cell_id: str = flow_cell.id
        self.lims_samples: List[FlowCellSample] = lims_samples
        self.run_parameters: RunParameters = flow_cell.run_parameters
        self.sample_type: Type[FlowCellSample] = flow_cell.sample_type
        self.force: bool = force

    @property
    def valid_indexes(self) -> List[Index]:
        return get_valid_indexes(dual_indexes_only=True)

    def remove_unwanted_samples(self) -> None:
        """Filter out samples with single indexes."""
        LOG.info("Removing all samples without dual indexes")
        samples_to_keep = []
        sample: FlowCellSample
        for sample in self.lims_samples:
            if not is_dual_index(sample.index):
                LOG.warning(f"Removing sample {sample} since it does not have dual index")
                continue
            samples_to_keep.append(sample)
        self.lims_samples = samples_to_keep

    @staticmethod
    def convert_sample_to_header_dict(
        sample: FlowCellSample,
        data_column_names: List[str],
    ) -> List[str]:
        """Convert a lims sample object to a list that corresponds to the sample sheet headers."""
        LOG.debug(f"Use sample sheet header {data_column_names}")
        sample_dict = sample.dict(by_alias=True)
        return [str(sample_dict[column]) for column in data_column_names]

    def get_additional_sections_sample_sheet(self) -> Optional[List]:
        """Return all sections of the sample sheet that are not the data section."""
        raise NotImplementedError("Impossible to get sample sheet sections from parent class")

    def get_data_section_header_and_columns(self) -> Optional[List[List[str]]]:
        """Return the header and column names of the data section of the sample sheet."""
        raise NotImplementedError("Impossible to get sample sheet sections from parent class")

    def create_sample_sheet_content(self) -> List[List[str]]:
        """Create sample sheet content with samples."""
        LOG.info("Creating sample sheet content")
        sample_sheet_content: List[List[str]] = (
            self.get_additional_sections_sample_sheet() + self.get_data_section_header_and_columns()
        )
        for sample in self.lims_samples:
            sample_sheet_content.append(
                self.convert_sample_to_header_dict(
                    sample=sample,
                    data_column_names=self.get_data_section_header_and_columns()[1],
                )
            )
        return sample_sheet_content

    def process_samples_for_sample_sheet(self) -> None:
        """Add dummy samples, remove unwanted samples and adapt remaining samples."""
        self.remove_unwanted_samples()
        samples_in_lane: List[FlowCellSample]
        reverse_complement: bool = is_reverse_complement(run_parameters=self.run_parameters)
        for lane, samples_in_lane in get_samples_by_lane(self.lims_samples).items():
            LOG.info(
                f"Adapting index and barcode mismatch values (if applicable) for samples in lane {lane}"
            )
            adapt_samples(
                samples=samples_in_lane,
                run_parameters=self.run_parameters,
                reverse_complement=reverse_complement,
            )

    def construct_sample_sheet(self) -> List[List[str]]:
        """Construct and validate the sample sheet."""
        self.process_samples_for_sample_sheet()
        sample_sheet_content: List[List[str]] = self.create_sample_sheet_content()
        if self.force:
            LOG.info("Skipping validation of sample sheet due to force flag")
            return sample_sheet_content
        LOG.info("Validating sample sheet")
        validate_sample_sheet(
            sample_sheet_content=sample_sheet_content,
            sample_type=self.sample_type,
        )
        LOG.info("Sample sheet passed validation")
        return sample_sheet_content


class SampleSheetCreatorV1(SampleSheetCreator):
    """Create a raw sample sheet for NovaSeq6000 flow cells."""

    def get_additional_sections_sample_sheet(self) -> List[List[str]]:
        """Return all sections of the sample sheet that are not the data section."""
        return [
            [SampleSheetNovaSeq6000Sections.Settings.HEADER.value],
            SampleSheetNovaSeq6000Sections.Settings.BARCODE_MISMATCH_INDEX1.value,
            SampleSheetNovaSeq6000Sections.Settings.BARCODE_MISMATCH_INDEX2.value,
        ]

    def get_data_section_header_and_columns(self) -> List[List[str]]:
        """Return the header and column names of the data section of the sample sheet."""
        return [
            [SampleSheetNovaSeq6000Sections.Data.HEADER.value],
            SampleSheetNovaSeq6000Sections.Data.COLUMN_NAMES.value[self.bcl_converter],
        ]


class SampleSheetCreatorV2(SampleSheetCreator):
    """Create a raw sample sheet for NovaSeqX flow cells."""

    def __init__(
        self,
        bcl_converter: str,
        flow_cell: FlowCellDirectoryData,
        lims_samples: List[FlowCellSample],
        force: bool = False,
    ):
        super().__init__(bcl_converter, flow_cell, lims_samples, force)
        if bcl_converter == BclConverter.BCL2FASTQ:
            raise SampleSheetError(f"Can't use {BclConverter.BCL2FASTQ} with sample sheet v2")
        self.bcl_converter: str = BclConverter.DRAGEN

    def get_additional_sections_sample_sheet(self) -> List[List[str]]:
        """Return all sections of the sample sheet that are not the data section."""
        header_section: List[List[str]] = [
            [SampleSheetNovaSeqXSections.Header.HEADER.value],
            SampleSheetNovaSeqXSections.Header.FILE_FORMAT.value,
            [SampleSheetNovaSeqXSections.Header.RUN_NAME.value, self.flow_cell_id],
            SampleSheetNovaSeqXSections.Header.INSTRUMENT_PLATFORM.value,
            SampleSheetNovaSeqXSections.Header.INDEX_ORIENTATION_FORWARD.value,
        ]
        reads_section: List[List[str]] = [
            [SampleSheetNovaSeqXSections.Reads.HEADER.value],
            [
                SampleSheetNovaSeqXSections.Reads.READ_CYCLES_1.value,
                self.run_parameters.get_read_1_cycles(),
            ],
            [
                SampleSheetNovaSeqXSections.Reads.READ_CYCLES_2.value,
                self.run_parameters.get_read_2_cycles(),
            ],
            [
                SampleSheetNovaSeqXSections.Reads.INDEX_CYCLES_1.value,
                self.run_parameters.get_index_1_cycles(),
            ],
            [
                SampleSheetNovaSeqXSections.Reads.INDEX_CYCLES_2.value,
                self.run_parameters.get_index_2_cycles(),
            ],
        ]
        settings_section: List[List[str]] = [
            [SampleSheetNovaSeqXSections.Settings.HEADER.value],
            SampleSheetNovaSeqXSections.Settings.SOFTWARE_VERSION.value,
            SampleSheetNovaSeqXSections.Settings.FASTQ_COMPRESSION_FORMAT.value,
        ]
        return header_section + reads_section + settings_section

    def get_data_section_header_and_columns(self) -> List[List[str]]:
        """Return the header and column names of the data section of the sample sheet."""
        return [
            [SampleSheetNovaSeqXSections.Data.HEADER.value],
            SampleSheetNovaSeqXSections.Data.COLUMN_NAMES.value,
        ]
