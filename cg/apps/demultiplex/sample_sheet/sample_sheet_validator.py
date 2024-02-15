"""Module with validator classes for the sample sheet."""

import logging
import re
from typing import Type

from pydantic import TypeAdapter

from cg.apps.demultiplex.sample_sheet.read_sample_sheet import (
    get_raw_samples,
    validate_samples_unique_per_lane,
)
from cg.apps.demultiplex.sample_sheet.sample_models import (
    FlowCellSample,
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.constants.demultiplexing import (
    NAME_TO_INDEX_SETTINGS,
    SampleSheetBcl2FastqSections,
    SampleSheetBCLConvertSections,
)
from cg.exc import OverrideCyclesError, SampleSheetError

LOG = logging.getLogger(__name__)

FORWARD_INDEX_CYCLE_PATTERN: str = r"I(\d+)N(\d+)"
REVERSE_INDEX_CYCLE_PATTERN: str = r"N(\d+)I(\d+)"


class SampleSheetValidator:
    """Class for validating the content of a sample sheet."""

    def __init__(self, content: list[list[str]]):
        """Instantiate the class with a sample sheet file path or sample sheet content."""
        self.content: list[list[str]] = content
        self.sample_type: Type[FlowCellSample] = self._get_sample_type()
        self.read1_cycles: int | None = None
        self.read2_cycles: int | None = None
        self.index1_cycles: int | None = None
        self.index2_cycles: int | None = None
        self.is_index2_reverse_complement: bool | None = None

    def _get_sample_type(self) -> Type[FlowCellSample]:
        """Return the sample type identified from the sample sheet content."""
        for row in self.content:
            if not row:
                continue
            if SampleSheetBCLConvertSections.Data.HEADER in row[0]:
                LOG.info("Sample sheet was generated for BCL Convert")
                return FlowCellSampleBCLConvert
            if SampleSheetBcl2FastqSections.Data.HEADER in row[0]:
                LOG.info("Sample sheet was generated for BCL2FASTQ")
                return FlowCellSampleBcl2Fastq
        message: str = "Could not determine sample sheet type"
        LOG.error(message)
        raise SampleSheetError(message)

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
        raw_samples: list[dict[str, str]] = get_raw_samples(self.content)
        validated_samples = TypeAdapter(list[self.sample_type]).validate_python(raw_samples)
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

    def validate_sample_sheet(self):
        """Call the proper validation depending of the sample sheet type."""
        if self.sample_type is FlowCellSampleBCLConvert:
            self.validate_bcl_convert()
        else:
            self.validate_samples()


class OverrideCyclesValidator:
    """Class for validating the override cycles value of a sample in a sample sheet."""

    def __init__(
        self,
        run_read1_cycles: int,
        run_read2_cycles: int,
        run_index1_cycles: int,
        run_index2_cycles: int | None,
        is_reverse_complement: bool,
    ):
        self.sample: dict[str, str] | None = None
        self.sample_cycles: list[str] | None = None
        self.sample_id: str | None = None
        self.run_read1_cycles: int = run_read1_cycles
        self.run_read2_cycles: int = run_read2_cycles
        self.run_index1_cycles: int = run_index1_cycles
        self.run_index2_cycles: int | None = run_index2_cycles
        self.is_reverse_complement: bool = is_reverse_complement

    @staticmethod
    def is_index_cycle_value_following_pattern(
        pattern: str, index_cycle: str, run_cycles: int, index_sequence: str
    ) -> bool:
        """
        Returns whether an index cycle string is following a valid cycle regex pattern and has
        consistent values. Valid patterns are 'I(\d+)N(\d+)' and 'N(\d+)I(\d+)'. Having consistent
        values means that the sum of the number of index characters (I) and the number of ignored
        characters (N) specified in the index cycle string is equal to the number of run cycles
        and the length of the index sequence is equal to the number of index characters (I).
        """
        match = re.match(pattern, index_cycle)
        if match:
            if pattern == FORWARD_INDEX_CYCLE_PATTERN:
                index_chars, ignored_chars = map(int, match.groups())
            elif pattern == REVERSE_INDEX_CYCLE_PATTERN:
                ignored_chars, index_chars = map(int, match.groups())
            else:
                LOG.warning(f"Pattern {pattern} is not a valid index cycle pattern")
                return False
            if index_chars + ignored_chars == run_cycles and len(index_sequence) == index_chars:
                return True
        return False

    def _validate_reads_cycles(self) -> None:
        """
        Determine if the sample read cycles are valid, i.e. if the sample read cycle values are
        equal to the respective run read cycles.
        Raises:
            OverrideCyclesError if the reads cycles are not valid.
        """
        read1_cycle: str = self.sample_cycles[0]
        read2_cycle: str = self.sample_cycles[-1]
        if (
            read1_cycle == f"Y{self.run_read1_cycles}"
            and read2_cycle == f"Y{self.run_read2_cycles}"
        ):
            return
        message: str = f"Incorrect read cycles {self.sample_cycles} for sample {self.sample_id}"
        LOG.error(message)
        raise OverrideCyclesError(message)

    def _validate_index1_cycles(self) -> None:
        """
        Determine if the sample index 1 cycle is valid, i.e., if the number of index characters in
        the override cycles coincides with the length of the index sequence and if the number of
        ignored characters in the override cycles matches the difference between the length of the
        index sequence and the number of run index1 cycles.
        Raises:
            OverrideCyclesError if the index 1 cycle is not valid.
        """
        index1_cycle: str = self.sample_cycles[1]
        if (
            self.run_index1_cycles == len(self.sample["Index"])
            and index1_cycle == f"I{self.run_index1_cycles}"
        ):
            return
        if self.is_index_cycle_value_following_pattern(
            pattern=FORWARD_INDEX_CYCLE_PATTERN,
            index_cycle=index1_cycle,
            run_cycles=self.run_index1_cycles,
            index_sequence=self.sample["Index"],
        ):
            return
        message: str = f"Incorrect index1 cycle {index1_cycle} for sample {self.sample_id}"
        LOG.error(message)
        raise OverrideCyclesError(message)

    def _validate_index2_cycles(self) -> None:
        """
        Determine if the index 2 cycle is valid, i.e., if the number of ignored and index characters
        correspond to the length of the sample index2 sequence and the number of run index2 cycles,
        or if the index cycles should be None.
        Raises:
            OverrideCyclesError if the index 2 cycle is not valid.
        """
        if not self.run_index2_cycles and len(self.sample_cycles) == 3:
            return
        index2_cycle: str = self.sample_cycles[2]
        if not self.sample["Index2"] and index2_cycle == f"N{self.run_index2_cycles}":
            return
        if (
            self.run_index2_cycles == len(self.sample["Index2"])
            and index2_cycle == f"I{self.run_index2_cycles}"
        ):
            return
        if self.is_reverse_complement and self.is_index_cycle_value_following_pattern(
            pattern=REVERSE_INDEX_CYCLE_PATTERN,
            index_cycle=index2_cycle,
            run_cycles=self.run_index2_cycles,
            index_sequence=self.sample["Index2"],
        ):
            return
        if not self.is_reverse_complement and self.is_index_cycle_value_following_pattern(
            pattern=FORWARD_INDEX_CYCLE_PATTERN,
            index_cycle=index2_cycle,
            run_cycles=self.run_index2_cycles,
            index_sequence=self.sample["Index2"],
        ):
            return
        message: str = f"Incorrect index2 cycle {index2_cycle} for sample {self.sample_id}"
        LOG.error(message)
        raise OverrideCyclesError(message)

    def validate_sample(
        self,
        sample: dict[str, str],
    ) -> None:
        """Determine if the override cycles are valid for a given sample."""
        self.sample = sample
        self.sample_cycles = sample["OverrideCycles"].split(";")
        self.sample_id = sample["Sample_ID"]
        self._validate_reads_cycles()
        self._validate_index1_cycles()
        self._validate_index2_cycles()
