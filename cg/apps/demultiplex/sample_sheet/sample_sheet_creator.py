""" Create a sample sheet for NovaSeq flow cells."""

import logging

from cg.apps.demultiplex.sample_sheet.read_sample_sheet import get_samples_by_lane
from cg.apps.demultiplex.sample_sheet.sample_models import IlluminaSampleIndexSetting
from cg.constants.demultiplexing import IndexSettings, SampleSheetBCLConvertSections
from cg.models.demultiplex.run_parameters import RunParameters
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData

LOG = logging.getLogger(__name__)


class SampleSheetCreator:
    """Base class for sample sheet creation for an Illumina run."""

    def __init__(
        self,
        run_directory_data: IlluminaRunDirectoryData,
        samples: list[IlluminaSampleIndexSetting],
    ):
        self.run_directory_data: IlluminaRunDirectoryData = run_directory_data
        self.flow_cell_id: str = run_directory_data.id
        self.samples: list[IlluminaSampleIndexSetting] = samples
        self.run_parameters: RunParameters = run_directory_data.run_parameters
        self.index_settings: IndexSettings = self.run_parameters.index_settings

    def convert_sample_to_header_dict(
        self,
        sample: IlluminaSampleIndexSetting,
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

    def get_additional_sections_sample_sheet(self) -> list[list[str]]:
        """Return all sections of the sample sheet that are not the data section."""
        header_section: list[list[str]] = [
            [SampleSheetBCLConvertSections.Header.HEADER.value],
            SampleSheetBCLConvertSections.Header.file_format(),
            [SampleSheetBCLConvertSections.Header.RUN_NAME.value, self.flow_cell_id],
            [
                SampleSheetBCLConvertSections.Header.INSTRUMENT_PLATFORM_TITLE.value,
                SampleSheetBCLConvertSections.Header.instrument_platform_sequencer().get(
                    self.run_directory_data.sequencer_type
                ),
            ],
            SampleSheetBCLConvertSections.Header.index_orientation_forward(),
            [SampleSheetBCLConvertSections.Header.INDEX_SETTINGS.value, self.index_settings.name],
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

    def create_sample_sheet_content(self) -> list[list[str]]:
        """Create sample sheet content with samples."""
        LOG.info("Creating sample sheet content")
        complete_data_section: list[list[str]] = self.get_data_section_header_and_columns()
        sample_sheet_content: list[list[str]] = (
            self.get_additional_sections_sample_sheet() + complete_data_section
        )
        for sample in self.samples:
            sample_sheet_content.append(
                self.convert_sample_to_header_dict(
                    sample=sample,
                    data_column_names=complete_data_section[1],
                )
            )
        return sample_sheet_content

    def process_samples_for_sample_sheet(self) -> None:
        """Remove unwanted samples and adapt remaining samples."""
        for sample in self.samples:
            sample.process_indexes(run_parameters=self.run_parameters)
        is_reverse_complement: bool = (
            self.index_settings.are_i5_override_cycles_reverse_complemented
        )
        for lane, samples_in_lane in get_samples_by_lane(self.samples).items():
            LOG.info(f"Updating barcode mismatch values for samples in lane {lane}")
            for sample in samples_in_lane:
                sample.update_barcode_mismatches(
                    samples_to_compare=samples_in_lane,
                    is_run_single_index=self.run_parameters.is_single_index,
                    is_reverse_complement=is_reverse_complement,
                )

    def construct_sample_sheet(self) -> list[list[str]]:
        """Construct and validate the sample sheet."""
        self.process_samples_for_sample_sheet()
        sample_sheet_content: list[list[str]] = self.create_sample_sheet_content()
        return sample_sheet_content
