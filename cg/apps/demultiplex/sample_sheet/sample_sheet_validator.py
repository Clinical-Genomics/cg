"""Module with validator classes for the sample sheet."""

import logging
from pathlib import Path
from typing import Type

from cg.apps.demultiplex.sample_sheet.override_cycles_validator import OverrideCyclesValidator
from cg.apps.demultiplex.sample_sheet.read_sample_sheet import (
    get_flow_cell_samples_from_content,
    get_raw_samples,
    get_sample_type,
    validate_samples_unique_per_lane,
)
from cg.apps.demultiplex.sample_sheet.sample_models import FlowCellSample, FlowCellSampleBCLConvert
from cg.apps.demultiplex.sample_sheet.sample_sheet_models import SampleSheet
from cg.constants.constants import FileFormat
from cg.constants.demultiplexing import NAME_TO_INDEX_SETTINGS, SampleSheetBCLConvertSections
from cg.exc import OverrideCyclesError, SampleSheetError
from cg.io.controller import ReadFile

LOG = logging.getLogger(__name__)


class SampleSheetValidator:
    """Class for validating the content of a sample sheet."""

    def __init__(self):
        """Instantiate the class with a sample sheet file path or sample sheet content."""
        self.content: list[list[str]] | None = None
        self.sample_type: Type[FlowCellSample] | None = None
        self.read1_cycles: int | None = None
        self.read2_cycles: int | None = None
        self.index1_cycles: int | None = None
        self.index2_cycles: int | None = None
        self.is_index2_reverse_complement: bool | None = None

    def set_sample_content(self, content: list[list[str]]) -> None:
        """Set the sample sheet content."""
        self.content = content

    def set_sample_type(self) -> None:
        """Set the local attribute sample type identified from the sample sheet content."""
        self.sample_type = get_sample_type(self.content)

    def validate_all_sections_present(self) -> None:
        """
        Returns whether the sample sheet has the four mandatory sections:
            - Header
            - Reads
            - BCLConvert Settings
            - BCLConvert Data
        Raises: SampleSheetError if the sample sheet does not have all the sections.
        """
        has_header: bool = [SampleSheetBCLConvertSections.Header.HEADER] in self.content
        has_cycles: bool = [SampleSheetBCLConvertSections.Reads.HEADER] in self.content
        has_settings: bool = [SampleSheetBCLConvertSections.Settings.HEADER] in self.content
        has_data: bool = [SampleSheetBCLConvertSections.Data.HEADER] in self.content
        if not all([has_header, has_cycles, has_settings, has_data]):
            message: str = "Sample sheet does not have all the necessary sections"
            LOG.error(message)
            raise SampleSheetError(message)

    def _get_index_settings_name(self) -> str:
        """Return the index settings from the sample sheet's header."""
        for row in self.content:
            if SampleSheetBCLConvertSections.Header.INDEX_SETTINGS in row:
                return row[1]
        message: str = "No index settings found in sample sheet"
        LOG.error(message)
        raise SampleSheetError(message)

    def set_is_index2_reverse_complement(self) -> None:
        """Return whether the index2 override cycles value is reverse-complemented."""
        settings_name: str = self._get_index_settings_name()
        self.is_index2_reverse_complement = NAME_TO_INDEX_SETTINGS[
            settings_name
        ].are_i5_override_cycles_reverse_complemented

    def _get_cycle(self, cycle_name: str, nullable: bool = False) -> int | None:
        """
        Return the cycle from the sample sheet given the cycle name. Set nullable to True to
        return None if the cycle is not found.
        Raises:
            SampleSheetError if the cycle is not found and nullable is False.
        """
        for row in self.content:
            if cycle_name in row:
                return int(row[1])
        if not nullable:
            message: str = f"No {cycle_name} found in sample sheet"
            LOG.error(message)
            raise SampleSheetError(message)

    def set_cycles(self):
        """Set values to the run cycle attributes."""
        self.read1_cycles = self._get_cycle(SampleSheetBCLConvertSections.Reads.READ_CYCLES_1)
        self.read2_cycles = self._get_cycle(SampleSheetBCLConvertSections.Reads.READ_CYCLES_2)
        self.index1_cycles = self._get_cycle(SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_1)
        self.index2_cycles = self._get_cycle(
            cycle_name=SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_2, nullable=True
        )

    def validate_samples(self) -> None:
        """
        Determine if the samples have the correct attributes and are not unique per lane.
            Raises:
            ValidationError if the samples do not have the correct attributes based on their model.
            SampleSheetError if the samples are not unique per lane.
        """
        validated_samples: list[FlowCellSample] = get_flow_cell_samples_from_content(self.content)
        validate_samples_unique_per_lane(validated_samples)

    def validate_override_cycles(self) -> None:
        """Determine if the samples' override cycles are valid.
        Raises:
            SampleSheetError if any of the samples' override cycles are not valid.
        """
        samples: list[dict[str, str]] = get_raw_samples(self.content)
        validator = OverrideCyclesValidator(
            run_read1_cycles=self.read1_cycles,
            run_read2_cycles=self.read2_cycles,
            run_index1_cycles=self.index1_cycles,
            run_index2_cycles=self.index2_cycles,
            is_reverse_complement=self.is_index2_reverse_complement,
        )
        for sample in samples:
            try:
                validator.validate_sample(sample)
            except OverrideCyclesError as error:
                raise SampleSheetError from error

    def validate_bcl_convert(self):
        """Determine if the BCLConvert sample sheet is valid, which means:
        - All sections are present
        - The index settings are specified in the sample sheet header
        - The read and index cycles are specified in the sample sheet's reads section
        - The samples have the correct attributes
        - The override cycles are valid
        """
        self.validate_all_sections_present()
        self.set_is_index2_reverse_complement()
        self.set_cycles()
        self.validate_samples()
        self.validate_override_cycles()

    def validate_sample_sheet_from_content(self, content: list[list[str]]) -> None:
        """Call the proper validation depending of the sample sheet type."""
        self.set_sample_content(content)
        self.set_sample_type()
        if self.sample_type is FlowCellSampleBCLConvert:
            self.validate_bcl_convert()
        else:
            self.validate_samples()

    def validate_sample_sheet_from_file(self, file_path: Path) -> None:
        """Validate a sample sheet given the path to the file."""
        self.validate_sample_sheet_from_content(
            ReadFile.get_content_from_file(file_format=FileFormat.CSV, file_path=file_path)
        )

    def get_sample_sheet_object_from_file(self, file_path: Path) -> SampleSheet:
        """Return a sample sheet object given the path to the file.
        Raises:
            SampleSheetError: If the sample sheet is not valid.
        """
        self.validate_sample_sheet_from_file(file_path)
        samples: list[FlowCellSample] = get_flow_cell_samples_from_content(self.content)
        return SampleSheet(samples=samples)
