import logging
from abc import abstractmethod

from pydantic import BaseModel, ConfigDict, Field

from cg.apps.demultiplex.sample_sheet.index import (
    MINIMUM_HAMMING_DISTANCE,
    get_hamming_distance_index_1,
    get_hamming_distance_index_2,
    get_reverse_complement_dna_seq,
    is_dual_index,
    is_padding_needed,
    pad_index_one,
    pad_index_two,
)
from cg.apps.demultiplex.sample_sheet.validators import SampleId
from cg.constants.constants import GenomeVersion
from cg.constants.demultiplexing import (
    CUSTOM_INDEX_TAIL,
    SampleSheetBcl2FastqSections,
    SampleSheetBCLConvertSections,
)
from cg.constants.symbols import EMPTY_STRING
from cg.exc import SampleSheetError
from cg.models.demultiplex.run_parameters import RunParameters

LOG = logging.getLogger(__name__)


class FlowCellSample(BaseModel):
    """Base class for flow cell samples."""

    lane: int
    sample_id: SampleId
    index: str
    index2: str = EMPTY_STRING
    model_config = ConfigDict(populate_by_name=True)

    def separate_indexes(self, is_run_single_index: bool) -> None:
        """Update values for index and index2 splitting the original LIMS dual index."""
        if is_dual_index(self.index):
            index1, index2 = self.index.split("-")
            self.index = index1.strip().replace(CUSTOM_INDEX_TAIL, EMPTY_STRING)
            self.index2 = index2.strip() if not is_run_single_index else EMPTY_STRING

    @abstractmethod
    def process_indexes(self, run_parameters: RunParameters):
        """Update index attributes with the final values for the sample sheet."""
        pass

    @abstractmethod
    def update_barcode_mismatches(
        self, samples_to_compare: list, is_run_single_index: bool, is_reverse_complement: bool
    ) -> None:
        """Update the barcode_mismatches_1 and barcode_mismatches_2 attributes."""
        pass


class FlowCellSampleBcl2Fastq(FlowCellSample):
    """Class that represents a Bcl2Fastq sample."""

    flowcell_id: str = Field("", alias=SampleSheetBcl2FastqSections.Data.FLOW_CELL_ID)
    lane: int = Field(..., alias=SampleSheetBcl2FastqSections.Data.LANE)
    sample_ref: str = Field(
        GenomeVersion.hg19, alias=SampleSheetBcl2FastqSections.Data.SAMPLE_REFERENCE
    )
    index: str = Field(..., alias=SampleSheetBcl2FastqSections.Data.INDEX_1)
    index2: str = Field("", alias=SampleSheetBcl2FastqSections.Data.INDEX_2)
    sample_name: str = Field(..., alias=SampleSheetBcl2FastqSections.Data.SAMPLE_NAME)
    control: str = Field("N", alias=SampleSheetBcl2FastqSections.Data.CONTROL)
    recipe: str = Field("R1", alias=SampleSheetBcl2FastqSections.Data.RECIPE)
    operator: str = Field("script", alias=SampleSheetBcl2FastqSections.Data.OPERATOR)

    sample_id: SampleId = Field(
        ..., alias=SampleSheetBcl2FastqSections.Data.SAMPLE_INTERNAL_ID_BCL2FASTQ
    )
    project: str = Field(..., alias=SampleSheetBcl2FastqSections.Data.SAMPLE_PROJECT_BCL2FASTQ)

    def _pad_indexes_if_necessary(self, run_parameters: RunParameters) -> None:
        index_length: int = len(self.index)
        if is_padding_needed(
            index1_cycles=run_parameters.get_index_1_cycles(),
            index2_cycles=run_parameters.get_index_2_cycles(),
            sample_index_length=index_length,
        ):
            LOG.debug("Padding indexes")
            self.index = pad_index_one(index_string=self.index)
            self.index2 = pad_index_two(
                index_string=self.index2,
                reverse_complement=run_parameters.index_settings.should_i5_be_reverse_complemented,
            )
            return
        LOG.debug(f"Padding not necessary for sample {self.sample_id}")

    def process_indexes(self, run_parameters: RunParameters):
        """Parses, pads and reverse complement the indexes if necessary."""
        reverse_index2: bool = run_parameters.index_settings.should_i5_be_reverse_complemented
        self.separate_indexes(is_run_single_index=run_parameters.is_single_index)
        self._pad_indexes_if_necessary(run_parameters=run_parameters)
        if reverse_index2:
            self.index2 = get_reverse_complement_dna_seq(self.index2)

    def update_barcode_mismatches(
        self, samples_to_compare: list, is_run_single_index: bool, is_reverse_complement: bool
    ) -> None:
        """No updating of barcode mismatch values for Bcl2Fastq samples."""
        LOG.debug(f"No updating of barcode mismatch values for Bcl2Fastq sample {self.sample_id}")


class FlowCellSampleBCLConvert(FlowCellSample):
    """Class that represents a BCLConvert sample."""

    lane: int = Field(..., alias=SampleSheetBCLConvertSections.Data.LANE)
    sample_id: SampleId = Field(..., alias=SampleSheetBCLConvertSections.Data.SAMPLE_INTERNAL_ID)
    index: str = Field(..., alias=SampleSheetBCLConvertSections.Data.INDEX_1)
    index2: str = Field(EMPTY_STRING, alias=SampleSheetBCLConvertSections.Data.INDEX_2)
    override_cycles: str = Field(
        EMPTY_STRING, alias=SampleSheetBCLConvertSections.Data.OVERRIDE_CYCLES
    )
    adapter_read_1: str = Field(
        EMPTY_STRING, alias=SampleSheetBCLConvertSections.Data.ADAPTER_READ_1
    )
    adapter_read_2: str = Field(
        EMPTY_STRING, alias=SampleSheetBCLConvertSections.Data.ADAPTER_READ_2
    )
    barcode_mismatches_1: int = Field(
        1, alias=SampleSheetBCLConvertSections.Data.BARCODE_MISMATCHES_1
    )
    barcode_mismatches_2: int | str = Field(
        1, alias=SampleSheetBCLConvertSections.Data.BARCODE_MISMATCHES_2
    )

    def _get_index1_override_cycles(self, len_index1_cycles: int) -> str:
        """Create the index 1 sub-string for the override cycles attribute."""
        len_index_1_sample: int = len(self.index)
        cycles_format: str = f"I{len_index1_cycles};"
        if len_index_1_sample < len_index1_cycles:
            cycles_format = f"I{len_index_1_sample}N{len_index1_cycles - len_index_1_sample};"
        return cycles_format

    def _get_index2_override_cycles(self, len_index2_cycles: int, reverse_cycle: bool) -> str:
        """Create the index 2 sub-string for the override cycles attribute."""
        len_index_2_sample: int = len(self.index2)
        cycles_format: str = f"I{len_index2_cycles};"
        if len_index2_cycles == 0:  # The run was single-index
            cycles_format = EMPTY_STRING
        elif len_index_2_sample == 0:  # The sample was single-index
            cycles_format = f"N{len_index2_cycles};"
        elif len_index_2_sample < len_index2_cycles:
            cycles_format = (
                f"N{len_index2_cycles-len_index_2_sample}I{len_index_2_sample};"
                if reverse_cycle
                else f"I{len_index_2_sample}N{len_index2_cycles - len_index_2_sample};"
            )
        return cycles_format

    def update_override_cycles(self, run_parameters: RunParameters) -> None:
        """Updates the override cycles attribute."""
        reverse_index2_cycles: bool = (
            run_parameters.index_settings.are_i5_override_cycles_reverse_complemented
        )
        read1_cycles: str = f"Y{run_parameters.get_read_1_cycles()};"
        read2_cycles: str = f"Y{run_parameters.get_read_2_cycles()}"
        index1_cycles: str = self._get_index1_override_cycles(run_parameters.get_index_1_cycles())
        index2_cycles: str = self._get_index2_override_cycles(
            len_index2_cycles=run_parameters.get_index_2_cycles(),
            reverse_cycle=reverse_index2_cycles,
        )
        self.override_cycles = read1_cycles + index1_cycles + index2_cycles + read2_cycles

    def _update_barcode_mismatches_1(
        self, samples_to_compare: list["FlowCellSampleBCLConvert"]
    ) -> None:
        """Assign zero to barcode_mismatches_1 if the hamming distance between self.index
        and the index1 of any sample in the lane is below the minimum threshold."""
        for sample in samples_to_compare:
            if self.sample_id == sample.sample_id:
                continue
            if (
                get_hamming_distance_index_1(sequence_1=self.index, sequence_2=sample.index)
                < MINIMUM_HAMMING_DISTANCE
            ):
                LOG.info(f"Turning barcode mismatch for index 1 to 0 for sample {self.sample_id}")
                self.barcode_mismatches_1 = 0
                break

    def _update_barcode_mismatches_2(
        self,
        samples_to_compare: list["FlowCellSampleBCLConvert"],
        is_reverse_complement: bool,
    ) -> None:
        """Assign zero to barcode_mismatches_2 if the hamming distance between self.index2
        and the index2 of any sample in the lane is below the minimum threshold.
        If the sample is single-indexed, assign 'na'."""
        if self.index2 == EMPTY_STRING and "-" not in self.index:
            LOG.info(f"Turning barcode mismatch for index 2 to 'na' for sample {self.sample_id}")
            self.barcode_mismatches_2 = "na"
            return
        for sample in samples_to_compare:
            if self.sample_id == sample.sample_id:
                continue
            if (
                get_hamming_distance_index_2(
                    sequence_1=self.index2,
                    sequence_2=sample.index2,
                    is_reverse_complement=is_reverse_complement,
                )
                < MINIMUM_HAMMING_DISTANCE
            ):
                LOG.info(f"Turning barcode mismatch for index 2 to 0 for sample {self.sample_id}")
                self.barcode_mismatches_2 = 0
                break

    def process_indexes(self, run_parameters: RunParameters):
        """Parse and reverse complement the indexes and updates override cycles."""
        self.separate_indexes(is_run_single_index=run_parameters.is_single_index)
        if run_parameters.index_settings.should_i5_be_reverse_complemented:
            self.index2 = get_reverse_complement_dna_seq(self.index2)
        self.update_override_cycles(run_parameters=run_parameters)

    def update_barcode_mismatches(
        self,
        samples_to_compare: list["FlowCellSampleBCLConvert"],
        is_run_single_index: bool,
        is_reverse_complement: bool,
    ) -> None:
        """Update barcode mismatch attributes comparing to the rest of the samples in the lane."""
        if not samples_to_compare:
            raise SampleSheetError("No samples to compare with to update barcode mismatch values")
        self._update_barcode_mismatches_1(samples_to_compare=samples_to_compare)
        if is_run_single_index:
            LOG.debug("Run is single-indexed, skipping barcode mismatch update for index 2")
            return
        self._update_barcode_mismatches_2(
            samples_to_compare=samples_to_compare, is_reverse_complement=is_reverse_complement
        )
