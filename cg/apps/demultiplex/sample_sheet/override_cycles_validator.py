import logging
import re

from cg.constants.demultiplexing import (
    FORWARD_INDEX_CYCLE_PATTERN,
    REVERSE_INDEX_CYCLE_PATTERN,
    SampleSheetBCLConvertSections,
)
from cg.exc import OverrideCyclesError

LOG = logging.getLogger(__name__)


class OverrideCyclesValidator:
    """Class for validating the override cycles value of a sample in a sample sheet."""

    def __init__(
        self,
        run_read1_cycles: int | None = None,
        run_read2_cycles: int | None = None,
        run_index1_cycles: int | None = None,
        run_index2_cycles: int | None = None,
        is_reverse_complement: bool | None = None,
    ):
        self.sample: dict[str, str] | None = None
        self.sample_cycles: list[str] | None = None
        self.sample_id: str | None = None
        self.run_read1_cycles: int | None = run_read1_cycles
        self.run_read2_cycles: int | None = run_read2_cycles
        self.run_index1_cycles: int | None = run_index1_cycles
        self.run_index2_cycles: int | None = run_index2_cycles
        self.is_reverse_complement: bool | None = is_reverse_complement

    def set_run_cycles(
        self,
        read1_cycles: int | None = None,
        read2_cycles: int | None = None,
        index1_cycles: int | None = None,
        index2_cycles: int | None = None,
    ) -> None:
        """Set the run cycles."""
        self.run_read1_cycles = read1_cycles
        self.run_read2_cycles = read2_cycles
        self.run_index1_cycles = index1_cycles
        self.run_index2_cycles = index2_cycles

    def set_reverse_complement(self, is_reverse_complement: bool) -> None:
        """Set the reverse complement."""
        self.is_reverse_complement = is_reverse_complement

    def set_attributes_from_sample(self, sample: dict[str, str]) -> None:
        """Set the sample, override cycles and sample id."""
        self.sample = sample
        self.sample_cycles = sample[SampleSheetBCLConvertSections.Data.OVERRIDE_CYCLES].split(";")
        self.sample_id = sample[SampleSheetBCLConvertSections.Data.SAMPLE_INTERNAL_ID]

    @staticmethod
    def _is_index_cycle_value_following_pattern(
        pattern: str, index_cycle: str, run_cycles: int, index_sequence: str
    ) -> bool:
        """
        Returns whether an index cycle string is following a valid cycle regex pattern and has
        consistent values. Valid patterns are 'I(\d+)N(\d+)' and 'N(\d+)I(\d+)'. Having consistent
        values means that the sum of the number of index characters (I) and the number of ignored
        characters (N) specified in the index cycle string is equal to the number of run cycles
        and the length of the index sequence is equal to the number of index characters (I).
        """
        match = re.fullmatch(pattern, index_cycle)
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
        Determine if the sample index 1 cycle is valid, i.e., if the number of index cycles is
        coherent with the run cycles and the index sequence length.
        Raises:
            OverrideCyclesError if the index 1 cycle is not valid.
        """
        index1_cycle: str = self.sample_cycles[1]
        if (
            self.run_index1_cycles == len(self.sample[SampleSheetBCLConvertSections.Data.INDEX_1])
            and index1_cycle == f"I{self.run_index1_cycles}"
        ):
            return
        if self._is_index_cycle_value_following_pattern(
            pattern=FORWARD_INDEX_CYCLE_PATTERN,
            index_cycle=index1_cycle,
            run_cycles=self.run_index1_cycles,
            index_sequence=self.sample[SampleSheetBCLConvertSections.Data.INDEX_1],
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
        if (
            not self.sample[SampleSheetBCLConvertSections.Data.INDEX_2]
            and index2_cycle == f"N{self.run_index2_cycles}"
        ):
            return
        if (
            self.run_index2_cycles == len(self.sample[SampleSheetBCLConvertSections.Data.INDEX_2])
            and index2_cycle == f"I{self.run_index2_cycles}"
        ):
            return
        if self.is_reverse_complement and self._is_index_cycle_value_following_pattern(
            pattern=REVERSE_INDEX_CYCLE_PATTERN,
            index_cycle=index2_cycle,
            run_cycles=self.run_index2_cycles,
            index_sequence=self.sample[SampleSheetBCLConvertSections.Data.INDEX_2],
        ):
            return
        if not self.is_reverse_complement and self._is_index_cycle_value_following_pattern(
            pattern=FORWARD_INDEX_CYCLE_PATTERN,
            index_cycle=index2_cycle,
            run_cycles=self.run_index2_cycles,
            index_sequence=self.sample[SampleSheetBCLConvertSections.Data.INDEX_2],
        ):
            return
        message: str = (
            f"Index2 cycle {index2_cycle} of sample {self.sample_id} "
            f"does not match with run cycle {self.run_index2_cycles} "
            f"and reverse complement set to {self.is_reverse_complement}"
        )
        LOG.error(message)
        raise OverrideCyclesError(message)

    def validate_sample(
        self,
        sample: dict[str, str],
    ) -> None:
        """Determine if the override cycles are valid for a given sample."""
        self.set_attributes_from_sample(sample)
        self._validate_reads_cycles()
        self._validate_index1_cycles()
        self._validate_index2_cycles()
