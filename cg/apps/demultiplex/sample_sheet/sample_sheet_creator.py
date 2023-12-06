""" Create a sample sheet for NovaSeq flow cells."""
import logging
from typing import Type

from packaging.version import parse

from cg.apps.demultiplex.sample_sheet.index import (
    Index,
    get_index_pair,
    get_valid_indexes,
    is_dual_index,
    update_barcode_mismatch_values_for_sample,
    update_indexes_for_samples,
)
from cg.apps.demultiplex.sample_sheet.models import (
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.apps.demultiplex.sample_sheet.read_sample_sheet import (
    get_samples_by_lane,
    get_validated_sample_sheet,
)
from cg.constants.demultiplexing import (
    NEW_NOVASEQ_CONTROL_SOFTWARE_VERSION,
    NEW_NOVASEQ_REAGENT_KIT_VERSION,
    NO_REVERSE_COMPLEMENTS,
    NOVASEQ_6000_POST_1_5_KITS,
    NOVASEQ_X_INDEX_SETTINGS,
    BclConverter,
    IndexSettings,
    SampleSheetBcl2FastqSections,
    SampleSheetBCLConvertSections,
)
from cg.constants.sequencing import Sequencers
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
        self.sample_type: Type[
            FlowCellSampleBCLConvert | FlowCellSampleBcl2Fastq
        ] = flow_cell.sample_type
        self.force: bool = force
        self.index_settings: IndexSettings = self._get_index_settings()

    def _get_index_settings(self) -> IndexSettings:
        """Returns the correct index-related settings for the run in question"""
        if self.run_parameters.sequencer == Sequencers.NOVASEQX:
            LOG.debug("Using NovaSeqX index settings")
            return NOVASEQ_X_INDEX_SETTINGS
        if self._is_novaseq6000_post_1_5_kit:
            LOG.debug("Using NovaSeq 6000 post 1.5 kits index settings")
            return NOVASEQ_6000_POST_1_5_KITS
        return NO_REVERSE_COMPLEMENTS

    @property
    def _is_novaseq6000_post_1_5_kit(self) -> bool:
        """
        Returns whether sequencing was performed after the 1.5 consumables kits where introduced.
        This is indicated by the software version and the reagent kit fields in the run parameters.
        """
        if self.run_parameters.sequencer != Sequencers.NOVASEQ:
            return False

        if parse(self.run_parameters.control_software_version) < parse(
            NEW_NOVASEQ_CONTROL_SOFTWARE_VERSION
        ):
            return False
        if parse(self.run_parameters.reagent_kit_version) < parse(NEW_NOVASEQ_REAGENT_KIT_VERSION):
            return False
        return True

    @property
    def bcl_converter(self) -> str:
        """Return the bcl converter used for demultiplexing."""
        return self.flow_cell.bcl_converter

    @property
    def valid_indexes(self) -> list[Index]:
        return get_valid_indexes(dual_indexes_only=True)

    def update_barcode_mismatch_values_for_samples(self, *args) -> None:
        """Updates barcode mismatch values for samples if applicable."""
        raise NotImplementedError(
            "Impossible to update sample barcode mismatches from parent class"
        )

    def add_override_cycles_to_samples(self) -> None:
        """Add override cycles attribute to samples if sample sheet is v2."""
        raise NotImplementedError("Impossible to add override cycles to samples from parent class")

    def remove_unwanted_samples(self) -> None:
        """Filter out samples with single indexes."""
        LOG.info("Removing all samples without dual indexes")
        samples_to_keep = []
        sample: FlowCellSampleBCLConvert | FlowCellSampleBcl2Fastq
        for sample in self.lims_samples:
            if not is_dual_index(sample.index):
                LOG.warning(f"Removing sample {sample} since it does not have dual index")
                continue
            samples_to_keep.append(sample)
        self.lims_samples = samples_to_keep

    @staticmethod
    def convert_sample_to_header_dict(
        sample: FlowCellSampleBCLConvert | FlowCellSampleBcl2Fastq,
        data_column_names: list[str],
    ) -> list[str]:
        """Convert a lims sample object to a list that corresponds to the sample sheet headers."""
        sample_dict = sample.model_dump(by_alias=True)
        return [str(sample_dict[column]) for column in data_column_names]

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
        self.remove_unwanted_samples()
        samples_in_lane: list[FlowCellSampleBCLConvert | FlowCellSampleBcl2Fastq]
        self.add_override_cycles_to_samples()
        for lane, samples_in_lane in get_samples_by_lane(self.lims_samples).items():
            LOG.info(f"Adapting index and barcode mismatch values for samples in lane {lane}")
            update_indexes_for_samples(
                samples=samples_in_lane,
                index_cycles=self.run_parameters.index_length,
                perform_reverse_complement=self.index_settings.should_i5_be_reverse_complimented,
                sequencer=self.run_parameters.sequencer,
            )
            self.update_barcode_mismatch_values_for_samples(samples_in_lane)

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

    def update_barcode_mismatch_values_for_samples(self, *args) -> None:
        """Return None for flow cells to be demultiplexed with Bcl2fastq."""
        LOG.debug("No barcode mismatch updating for Bcl2fastq flow cell")

    def add_override_cycles_to_samples(self) -> None:
        """Return None for flow cells to be demultiplexed with Bcl2fastq."""
        LOG.debug("Skipping adding of override cycles for Bcl2fastq flow cell")

    def get_additional_sections_sample_sheet(self) -> list[list[str]]:
        """Return all sections of the sample sheet that are not the data section."""
        return [
            [SampleSheetBcl2FastqSections.Settings.HEADER],
            SampleSheetBcl2FastqSections.Settings.barcode_mismatch_index_1(),
            SampleSheetBcl2FastqSections.Settings.barcode_mismatch_index_2(),
        ]

    def get_data_section_header_and_columns(self) -> list[list[str]]:
        """Return the header and column names of the data section of the sample sheet."""
        return [
            [SampleSheetBcl2FastqSections.Data.HEADER.value],
            SampleSheetBcl2FastqSections.Data.column_names(),
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

    def update_barcode_mismatch_values_for_samples(
        self, samples: list[FlowCellSampleBCLConvert]
    ) -> None:
        """Update barcode mismatch values for both indexes of given samples."""
        for sample in samples:
            update_barcode_mismatch_values_for_sample(
                sample_to_update=sample, samples_to_compare_to=samples
            )

    def add_override_cycles_to_samples(self) -> None:
        """Add override cycles attribute to samples."""
        read1_cycles: str = f"Y{self.run_parameters.get_read_1_cycles()};"
        read2_cycles: str = f"Y{self.run_parameters.get_read_2_cycles()}"
        length_index1: int = self.run_parameters.get_index_1_cycles()
        length_index2: int = self.run_parameters.get_index_2_cycles()
        for sample in self.lims_samples:
            index1_cycles: str = f"I{length_index1};"
            index2_cycles: str = f"I{length_index2};"
            sample_index1_len: int = len(get_index_pair(sample)[0])
            sample_index2_len: int = len(get_index_pair(sample)[1])
            if sample_index1_len < length_index1:
                index1_cycles = f"I{sample_index1_len}N{length_index1 - sample_index1_len};"
            if sample_index2_len < length_index2:
                index2_cycles = (
                    f"N{length_index2-sample_index2_len}I{sample_index2_len};"
                    if self.index_settings.are_i5_override_cycles_reverse_complemented
                    else f"I{sample_index2_len}N{length_index2 - sample_index2_len};"
                )
            sample.override_cycles = read1_cycles + index1_cycles + index2_cycles + read2_cycles

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
            [
                SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_2,
                self.run_parameters.get_index_2_cycles(),
            ],
        ]
        settings_section: list[list[str]] = [
            [SampleSheetBCLConvertSections.Settings.HEADER],
            SampleSheetBCLConvertSections.Settings.software_version(),
            SampleSheetBCLConvertSections.Settings.fastq_compression_format(),
        ]
        return header_section + reads_section + settings_section

    def get_data_section_header_and_columns(self) -> list[list[str]]:
        """Return the header and column names of the data section of the sample sheet."""
        return [
            [SampleSheetBCLConvertSections.Data.HEADER.value],
            SampleSheetBCLConvertSections.Data.column_names(),
        ]
