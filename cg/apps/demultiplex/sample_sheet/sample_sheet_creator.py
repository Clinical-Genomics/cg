""" Create a sample sheet for NovaSeq flow cells."""

import logging
from abc import abstractmethod
from typing import Type

from cg.apps.demultiplex.sample_sheet.index import (
    Index,
    get_valid_indexes,
    is_dual_index,
)
from cg.apps.demultiplex.sample_sheet.read_sample_sheet import (
    get_samples_by_lane,
    get_validated_sample_sheet,
)
from cg.apps.demultiplex.sample_sheet.sample_models import (
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.constants.demultiplexing import (
    BclConverter,
    IndexSettings,
    SampleSheetBcl2FastqSections,
    SampleSheetBCLConvertSections,
)
from cg.exc import SampleSheetError
from cg.models.demultiplex.run_parameters import RunParameters
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData

LOG = logging.getLogger(__name__)


class SampleSheetCreator:
    """Base class for sample sheet creation."""

    def __init__(
        self,
        flow_cell: FlowCellDirectoryData,
        lims_samples: list[FlowCellSampleBCLConvert | FlowCellSampleBcl2Fastq],
        force: bool = False,
    ):
        self.flow_cell: FlowCellDirectoryData = flow_cell
        self.flow_cell_id: str = flow_cell.id
        self.lims_samples: list[FlowCellSampleBCLConvert | FlowCellSampleBcl2Fastq] = lims_samples
        self.run_parameters: RunParameters = flow_cell.run_parameters
        self.sample_type: Type[FlowCellSampleBCLConvert | FlowCellSampleBcl2Fastq] = (
            flow_cell.sample_type
        )
        self.force: bool = force
        self.index_settings: IndexSettings = self.run_parameters.index_settings

    @property
    def bcl_converter(self) -> str:
        """Return the bcl converter used for demultiplexing."""
        return self.flow_cell.bcl_converter

    @property
    def valid_indexes(self) -> list[Index]:
        return get_valid_indexes(dual_indexes_only=True)

    @abstractmethod
    def remove_samples_with_simple_index(self) -> None:
        """Filter out samples with single indexes."""
        pass

    def convert_sample_to_header_dict(
        self,
        sample: FlowCellSampleBCLConvert | FlowCellSampleBcl2Fastq,
        data_column_names: list[str],
    ) -> list[str]:
        """Convert a lims sample object to a list that corresponds to the sample sheet headers."""
        if self.run_parameters.is_single_index:
            sample_serialisation: dict = sample.model_dump(
                by_alias=True, exclude={"index2", "barcode_mismatches_2"}
            )
        else:
            sample_serialisation: dict = sample.model_dump(by_alias=True)

        return [str(sample_serialisation[column_name]) for column_name in data_column_names]

    def get_additional_sections_sample_sheet(self) -> list | None:
        """Return all sections of the sample sheet that are not the data section."""
        raise NotImplementedError("Impossible to get sample sheet sections from parent class")

    def get_data_section_header_and_columns(self) -> list[list[str]] | None:
        """Return the header and column names of the data section of the sample sheet."""
        raise NotImplementedError("Impossible to get sample sheet sections from parent class")

    def create_sample_sheet_content(self) -> list[list[str]]:
        """Create sample sheet content with samples."""
        LOG.info("Creating sample sheet content")
        complete_data_section: list[list[str]] = self.get_data_section_header_and_columns()
        sample_sheet_content: list[list[str]] = (
            self.get_additional_sections_sample_sheet() + complete_data_section
        )
        LOG.debug(f"Use sample sheet header {complete_data_section[1]}")
        for sample in self.lims_samples:
            sample_sheet_content.append(
                self.convert_sample_to_header_dict(
                    sample=sample,
                    data_column_names=complete_data_section[1],
                )
            )
        return sample_sheet_content

    def process_samples_for_sample_sheet(self) -> None:
        """Remove unwanted samples and adapt remaining samples."""
        self.remove_samples_with_simple_index()
        for lims_sample in self.lims_samples:
            lims_sample.process_indexes(run_parameters=self.run_parameters)
        for lane, samples_in_lane in get_samples_by_lane(self.lims_samples).items():
            LOG.info(f"Updating barcode mismatch values for samples in lane {lane}")
            for lims_sample in samples_in_lane:
                lims_sample.update_barcode_mismatches(
                    samples_to_compare=samples_in_lane,
                    is_run_single_index=self.run_parameters.is_single_index,
                    is_reverse_complement=self.index_settings.are_i5_override_cycles_reverse_complemented,
                )

    def construct_sample_sheet(self) -> list[list[str]]:
        """Construct and validate the sample sheet."""
        self.process_samples_for_sample_sheet()
        sample_sheet_content: list[list[str]] = self.create_sample_sheet_content()
        if self.force:
            LOG.info("Skipping validation of sample sheet due to force flag")
            return sample_sheet_content
        LOG.info("Validating sample sheet")
        get_validated_sample_sheet(
            sample_sheet_content=sample_sheet_content,
            sample_type=self.sample_type,
        )
        LOG.info("Sample sheet passed validation")
        return sample_sheet_content


class SampleSheetCreatorBcl2Fastq(SampleSheetCreator):
    """Create a raw sample sheet for flow cells."""

    def remove_samples_with_simple_index(self) -> None:
        """Filter out samples with single indexes."""
        LOG.info("Removing all samples without dual indexes")
        samples_to_keep: list[FlowCellSampleBcl2Fastq] = []
        for sample in self.lims_samples:
            if not is_dual_index(sample.index):
                LOG.warning(f"Removing sample {sample.sample_id} since it does not have dual index")
                continue
            samples_to_keep.append(sample)
        self.lims_samples = samples_to_keep

    def get_additional_sections_sample_sheet(self) -> list[list[str]]:
        """Return all sections of the sample sheet that are not the data section."""
        return [
            [SampleSheetBcl2FastqSections.Settings.HEADER],
            SampleSheetBcl2FastqSections.Settings.barcode_mismatch_index_1(),
            SampleSheetBcl2FastqSections.Settings.barcode_mismatch_index_2(),
        ]

    def get_data_section_header_and_columns(self) -> list[list[str]]:
        """Return the header and column names of the data section of the sample sheet."""
        column_names: list[str] = SampleSheetBcl2FastqSections.Data.column_names()
        if self.run_parameters.is_single_index:
            column_names.remove(SampleSheetBcl2FastqSections.Data.INDEX_2)
        return [
            [SampleSheetBcl2FastqSections.Data.HEADER.value],
            column_names,
        ]


class SampleSheetCreatorBCLConvert(SampleSheetCreator):
    """Create a raw sample sheet for BCLConvert flow cells."""

    def __init__(
        self,
        flow_cell: FlowCellDirectoryData,
        lims_samples: list[FlowCellSampleBCLConvert],
        force: bool = False,
    ):
        super().__init__(flow_cell, lims_samples, force)
        if flow_cell.bcl_converter == BclConverter.BCL2FASTQ:
            raise SampleSheetError(f"Can't use {BclConverter.BCL2FASTQ} with sample sheet v2")

    def remove_samples_with_simple_index(self) -> None:
        """Filter out samples with single indexes."""
        LOG.info("Removing of single index samples is not required for V2 sample sheet")

    def get_additional_sections_sample_sheet(self) -> list[list[str]]:
        """Return all sections of the sample sheet that are not the data section."""
        header_section: list[list[str]] = [
            [SampleSheetBCLConvertSections.Header.HEADER.value],
            SampleSheetBCLConvertSections.Header.file_format(),
            [SampleSheetBCLConvertSections.Header.RUN_NAME.value, self.flow_cell_id],
            [
                SampleSheetBCLConvertSections.Header.INSTRUMENT_PLATFORM_TITLE.value,
                SampleSheetBCLConvertSections.Header.instrument_platform_sequencer().get(
                    self.flow_cell.sequencer_type
                ),
            ],
            SampleSheetBCLConvertSections.Header.index_orientation_forward(),
        ]
        reads_section: list[list[str]] = [
            [SampleSheetBCLConvertSections.Reads.HEADER],
            [
                SampleSheetBCLConvertSections.Reads.READ_CYCLES_1,
                self.run_parameters.get_read_1_cycles(),
            ],
            [
                SampleSheetBCLConvertSections.Reads.READ_CYCLES_2,
                self.run_parameters.get_read_2_cycles(),
            ],
            [
                SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_1,
                self.run_parameters.get_index_1_cycles(),
            ],
        ]
        if not self.run_parameters.is_single_index:
            reads_section.append(
                [
                    SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_2,
                    self.run_parameters.get_index_2_cycles(),
                ]
            )
        settings_section: list[list[str]] = [
            [SampleSheetBCLConvertSections.Settings.HEADER],
            SampleSheetBCLConvertSections.Settings.software_version(),
            SampleSheetBCLConvertSections.Settings.fastq_compression_format(),
        ]
        return header_section + reads_section + settings_section

    def get_data_section_header_and_columns(self) -> list[list[str]]:
        """Return the header and column names of the data section of the sample sheet."""
        column_names: list[str] = SampleSheetBCLConvertSections.Data.column_names()
        if self.run_parameters.is_single_index:
            column_names.remove(SampleSheetBCLConvertSections.Data.BARCODE_MISMATCHES_2)
            column_names.remove(SampleSheetBCLConvertSections.Data.INDEX_2)
        return [
            [SampleSheetBCLConvertSections.Data.HEADER],
            column_names,
        ]
