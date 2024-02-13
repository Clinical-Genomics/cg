import logging
import re
from pathlib import Path
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
from cg.constants.constants import FileFormat
from cg.constants.demultiplexing import (
    NO_REVERSE_COMPLEMENTS_INDEX_SETTINGS,
    NOVASEQ_6000_POST_1_5_KITS_INDEX_SETTINGS,
    NOVASEQ_X_INDEX_SETTINGS,
    IndexSettings,
    SampleSheetBcl2FastqSections,
    SampleSheetBCLConvertSections,
)
from cg.exc import SampleSheetError
from cg.io.controller import ReadFile

LOG = logging.getLogger(__name__)

NAME_TO_INDEX_SETTINGS: dict[str, IndexSettings] = {
    "NovaSeqX": NOVASEQ_X_INDEX_SETTINGS,
    "NovaSeq6000Post1.5Kits": NOVASEQ_6000_POST_1_5_KITS_INDEX_SETTINGS,
    "NoReverseComplements": NO_REVERSE_COMPLEMENTS_INDEX_SETTINGS,
}


class SampleSheetValidator:
    def __init__(self, sample_sheet_path: Path):
        if sample_sheet_path.exists():
            self.path: Path = sample_sheet_path
        else:
            raise SampleSheetError(f"Sample sheet file {sample_sheet_path} does not exist")
        self.content: list[list[str]] = ReadFile.get_content_from_file(
            file_format=FileFormat.CSV, file_path=sample_sheet_path
        )
        self.sample_type: Type[FlowCellSample] = self.get_sample_type()
        self.read1_cycles: int | None = None
        self.read2_cycles: int | None = None
        self.index1_cycles: int | None = None
        self.index2_cycles: int | None = None

    def _get_index_settings(self) -> str:
        """Return the index settings from the sample sheet."""
        for row in self.content:
            if SampleSheetBCLConvertSections.Header.INDEX_SETTINGS in row:
                return row[1]
        raise SampleSheetError("No index settings found in sample sheet")

    @property
    def index_settings(self) -> IndexSettings:
        """Return the index settings from the sample sheet."""
        settings_name: str = self._get_index_settings()
        return NAME_TO_INDEX_SETTINGS[settings_name]

    def _get_cycle(self, cycle_name: str) -> int:
        """Return the cycle from the sample sheet."""
        for row in self.content:
            if cycle_name in row:
                return int(row[1])

    def set_cycles(self):
        """Set values to the cycle attributes."""
        self.read1_cycles = self._get_cycle(SampleSheetBCLConvertSections.Reads.READ_CYCLES_1)
        self.read2_cycles = self._get_cycle(SampleSheetBCLConvertSections.Reads.READ_CYCLES_2)
        self.index1_cycles = self._get_cycle(SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_1)
        self.index2_cycles = self._get_cycle(SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_2)

    def get_sample_type(self) -> Type[FlowCellSample]:
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
        raise SampleSheetError("Could not determine sample sheet type")

    def _core_validate(self) -> None:
        """
        Determine if the samples have the correct form.
            Raises:
            ValidationError if the samples do not have the correct attributes based on their model.
            SampleSheetError if the samples are not unique per lane.
        """
        raw_samples: list[dict[str, str]] = get_raw_samples(self.content)
        validated_samples = TypeAdapter(list[self.sample_type]).validate_python(raw_samples)
        validate_samples_unique_per_lane(validated_samples)

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
            raise SampleSheetError("Sample sheet does not have all the necessary sections")

    def _validate_reads_cycles(self, cycles: list[str], sample_id: str) -> None:
        """Determine if the reads cycles are valid."""
        if cycles[0] != f"Y{self.read1_cycles}" or cycles[-1] != f"Y{self.read2_cycles}":
            message: str = f"Override cycles don't match with read cycles for sample {sample_id}"
            LOG.error(message)
            raise SampleSheetError(message)

    def _validate_index1_cycles(self, index1_cycle: str, sample_id: str) -> None:
        """Determine if the index 1 cycles are valid."""
        if index1_cycle == f"I{self.index1_cycles}":
            return
        pattern = r"I(\d+)N(\d+)"
        match = re.match(pattern, index1_cycle)
        if match:
            a, b = map(int, match.groups())
            if a + b == self.index1_cycles:
                return
        message: str = f"Incorrect index1 cycle {index1_cycle} for sample {sample_id}"
        LOG.error(message)
        raise SampleSheetError(message)

    def _validate_single_override_cycles(self, sample: dict[str, str]) -> None:
        """Determine if a single override cycle is valid."""
        cycles: list[str] = sample["OverrideCycles"].split(";")
        sample_id: str = sample["Sample_ID"]
        self._validate_reads_cycles(cycles=cycles, sample_id=sample_id)
        self._validate_index1_cycles(index1_cycle=cycles[1], sample_id=sample_id)

    def validate_override_cycles(self) -> None:
        """Determine if the samples' override cycles are valid.
        Raises:
            SampleSheetError if the samples' override cycles are not valid.
        """
        samples: list[dict[str, str]] = get_raw_samples(self.content)
        for sample in samples:
            override_cycles: list[str] = sample["OverrideCycles"].split(";")
            if len(override_cycles) != 4:
                raise SampleSheetError("OverrideCycles must have 4 values")
            for cycle in override_cycles:
                if not cycle.isdigit():
                    raise SampleSheetError("OverrideCycles must have integer values")

    def _validate_bcl_convert(self):
        """Determine if the BCLConvert sample sheet is valid.
        Raises:
            ValidationError if the sample sheet has not the correct structure.
        """
        self._core_validate()
        self.validate_all_sections_present()

    def validate(self):
        """
        Determine if the sample sheet is valid.
        Raises:
            ValidationError if the sample sheet has not the correct structure
        """
        if self.sample_type is FlowCellSampleBCLConvert:
            self._validate_bcl_convert()
        else:
            self._core_validate()
