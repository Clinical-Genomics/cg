"""Class to create a new sample sheet for a flow cell."""

import logging
from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.apps.lims.sample_sheet import get_flow_cell_samples
from cg.constants.demultiplexing import SampleSheetBCLConvertSections
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.sample_sheet.models import (
    IlluminaSampleIndexSetting,
    SampleSheet,
    SampleSheetData,
    SampleSheetHeader,
    SampleSheetReads,
    SampleSheetSettings,
)
from cg.services.illumina.sample_sheet.validator import SampleSheetValidator

LOG = logging.getLogger(__name__)


class SampleSheetCreator:

    def __init__(self, sequencing_dir: str, lims_api: LimsAPI, validator: SampleSheetValidator):
        self.sequencing_dir = Path(sequencing_dir)
        self.lims_api = lims_api
        self.validator = validator

    def create(self, run_dir: IlluminaRunDirectoryData) -> SampleSheet:
        """Get a sample sheet from Housekeeper, flow cell dir or create a new one."""
        header: SampleSheetHeader = self._create_header_section(run_dir)
        reads: SampleSheetReads = self._create_reads_section(run_dir)
        settings: SampleSheetSettings = self._create_settings_section()
        data: SampleSheetData = self._create_data_section(lims_samples)
        return SampleSheet(header=header, reads=reads, settings=settings, data=data)

    @staticmethod
    def _create_header_section(run_dir: IlluminaRunDirectoryData) -> SampleSheetHeader:
        """Create the header section of the sample sheet."""
        return SampleSheetHeader(
            version=SampleSheetBCLConvertSections.Header.file_format(),
            run_name=[SampleSheetBCLConvertSections.Header.RUN_NAME, run_dir.id],
            instrument=[
                SampleSheetBCLConvertSections.Header.INSTRUMENT_PLATFORM_TITLE,
                SampleSheetBCLConvertSections.Header.instrument_platform_sequencer().get(
                    run_dir.sequencer_type
                ),
            ],
            index_orientation=SampleSheetBCLConvertSections.Header.index_orientation_forward(),
            index_settings=[
                SampleSheetBCLConvertSections.Header.INDEX_SETTINGS.value,
                run_dir.run_parameters.index_settings.name,
            ],
        )

    @staticmethod
    def _create_reads_section(run_dir: IlluminaRunDirectoryData) -> SampleSheetReads:
        """Create the reads section of the sample sheet."""
        reads_section: dict = {
            "read_1": [
                SampleSheetBCLConvertSections.Reads.READ_CYCLES_1,
                run_dir.run_parameters.get_read_1_cycles(),
            ],
            "read_2": [
                SampleSheetBCLConvertSections.Reads.READ_CYCLES_2,
                run_dir.run_parameters.get_read_2_cycles(),
            ],
            "index_1": [
                SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_1,
                run_dir.run_parameters.get_index_1_cycles(),
            ],
        }
        if not run_dir.run_parameters.is_single_index:
            reads_section["index_2"] = [
                SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_2,
                run_dir.run_parameters.get_index_2_cycles(),
            ]
        return SampleSheetReads.model_validate(reads_section)

    @staticmethod
    def _create_settings_section() -> SampleSheetSettings:
        """Create the settings section of the sample sheet."""
        return SampleSheetSettings(
            software_version=SampleSheetBCLConvertSections.Settings.software_version(),
            compression_format=SampleSheetBCLConvertSections.Settings.fastq_compression_format(),
        )

    def _create_data_section(self, run_dir: IlluminaRunDirectoryData) -> SampleSheetData:
        """Create the data section of the sample sheet."""
        column_names: list[str] = SampleSheetBCLConvertSections.Data.column_names()
        if run_dir.run_parameters.is_single_index:
            column_names.remove(SampleSheetBCLConvertSections.Data.BARCODE_MISMATCHES_2)
            column_names.remove(SampleSheetBCLConvertSections.Data.INDEX_2)
        lims_samples: list[IlluminaSampleIndexSetting] = list(
            get_flow_cell_samples(
                lims=self.lims_api,
                flow_cell_id=run_dir.id,
            )
        )
        return SampleSheetData(
            columns=SampleSheetBCLConvertSections.Data.column_names(),
            samples=lims_samples,
        )
