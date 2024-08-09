import logging

from cg.constants.symbols import EMPTY_STRING
from cg.models.demultiplex.run_parameters import RunParameters
from cg.services.illumina.sample_sheet.models import IlluminaSampleIndexSetting
from cg.services.illumina.sample_sheet.utils import (
    MINIMUM_HAMMING_DISTANCE,
    get_hamming_distance_index_1,
    get_hamming_distance_index_2,
    get_reverse_complement_dna_seq,
)

LOG = logging.getLogger(__name__)


class SamplesUpdater:
    """Class to update a sample with the override cycles and barcode mismatches attributes."""

    def __init__(self):
        self.samples: list[IlluminaSampleIndexSetting] | None = None
        self.run_parameters: RunParameters | None = None

    def update_all_samples(
        self, samples: list[IlluminaSampleIndexSetting], run_parameters: RunParameters
    ) -> None:
        """Update all samples with the override cycles and barcode mismatch attributes."""
        self.samples = samples
        self.run_parameters = run_parameters
        for sample in self.samples:
            self._update_sample(sample)

    def _update_sample(self, sample: IlluminaSampleIndexSetting) -> None:
        self._reverse_index2_if_necessary(sample)
        self._update_override_cycles(sample)
        self._update_barcode_mismatches(sample)

    def _reverse_index2_if_necessary(self, sample: IlluminaSampleIndexSetting) -> None:
        """Reverse complement the index 2 attribute of a sample if necessary."""
        if sample.index2 and self.run_parameters.index_settings.should_i5_be_reverse_complemented:
            sample.index2 = get_reverse_complement_dna_seq(sample.index2)

    def _update_override_cycles(self, sample: IlluminaSampleIndexSetting) -> None:
        read1_cycles: str = f"Y{self.run_parameters.get_read_1_cycles()};"
        read2_cycles: str = f"Y{self.run_parameters.get_read_2_cycles()}"
        index1_cycles: str = self._get_index1_override_cycles(sample)
        index2_cycles: str = self._get_index2_override_cycles(sample)
        self.override_cycles = read1_cycles + index1_cycles + index2_cycles + read2_cycles

    def _get_index1_override_cycles(self, sample: IlluminaSampleIndexSetting) -> str:
        """Create the index 1 sub-string of the override cycles attribute for a sample."""
        len_index1_cycles = self.run_parameters.get_index_1_cycles()
        if not sample.index:  # Non-indexed sample
            return f"N{len_index1_cycles};"
        len_index_1_sample: int = len(sample.index)
        if len_index_1_sample < len_index1_cycles:
            return f"I{len_index1_cycles}N{len_index1_cycles - len_index_1_sample};"
        return f"I{len_index1_cycles};"

    def _get_index2_override_cycles(self, sample: IlluminaSampleIndexSetting) -> str:
        """Create the index 2 sub-string of the override cycles attribute for a sample."""
        len_index2_cycles: int = self.run_parameters.get_index_2_cycles()
        if len_index2_cycles == 0:  # The run was single-index
            return EMPTY_STRING
        if not sample.index2:  # The sample was single-index
            return f"N{len_index2_cycles};"
        len_index_2_sample: int = len(sample.index2)
        if len_index2_cycles == len_index_2_sample:  # All index cycles are considered
            return f"I{len_index2_cycles};"
        ignored_cycles: str = f"N{len_index2_cycles-len_index_2_sample}"
        considered_cycles: str = f"I{len_index_2_sample}"
        if self.run_parameters.index_settings.are_i5_override_cycles_reverse_complemented:
            return f"{ignored_cycles}{considered_cycles};"
        return f"{considered_cycles}{ignored_cycles};"

    def _update_barcode_mismatches(self, sample: IlluminaSampleIndexSetting) -> None:
        """Update the barcode mismatches attributes of a sample."""
        self._update_barcode_mismatches_1(sample)
        self._update_barcode_mismatches_2(sample)

    def _update_barcode_mismatches_1(self, sample: IlluminaSampleIndexSetting) -> None:
        """Update the barcode mismatches 1 attribute of a sample."""
        if not sample.index:
            return
        if self._is_index_1_similar_to_other_samples(sample):
            sample.barcode_mismatches_1 = 0
        sample.barcode_mismatches_1 = 1

    def _is_index_1_similar_to_other_samples(self, sample: IlluminaSampleIndexSetting) -> bool:
        """
        Check whether the index 1 from a given sample is too similar to the index 1 sequences of any
        other sample of the same lane in the sample sheet. Two indexes are too similar if the
        Hamming distance between them is below the minimum allowed by the demultiplexing software.
        """
        samples_to_compare: list[IlluminaSampleIndexSetting] = self._get_samples_by_lane(
            samples=self.samples, lane=sample.lane
        )
        for sample_to_compare in samples_to_compare:
            if sample.sample_id == sample_to_compare.sample_id:
                continue
            distance: int = get_hamming_distance_index_1(
                sequence_1=sample.index, sequence_2=sample_to_compare.index
            )
            if distance < MINIMUM_HAMMING_DISTANCE:
                return True
        return False

    def _update_barcode_mismatches_2(self, sample: IlluminaSampleIndexSetting) -> None:
        """Assign zero to barcode_mismatches_2 if the hamming distance between self.index2
        and the index2 of any sample in the lane is below the minimum threshold.
        If the sample is single-indexed, assign 'na'."""
        if self.run_parameters.is_single_index:
            return
        if not sample.index2:
            sample.barcode_mismatches_2 = "na"
        if self._is_index_2_similar_to_other_samples(sample):
            sample.barcode_mismatches_2 = 0
        sample.barcode_mismatches_2 = 1

    def _is_index_2_similar_to_other_samples(self, sample: IlluminaSampleIndexSetting) -> bool:
        """
        Check whether the index 2 from a given sample is too similar to the index 2 sequences of any
        other sample of the same lane in the sample sheet. Two indexes are too similar if the
        Hamming distance between them is below the minimum allowed by the demultiplexing software.
        """
        is_run_reverse_complement: bool = (
            self.run_parameters.index_settings.should_i5_be_reverse_complemented
        )
        samples_to_compare: list[IlluminaSampleIndexSetting] = self._get_samples_by_lane(
            samples=self.samples, lane=sample.lane
        )
        for sample_to_compare in samples_to_compare:
            if sample.sample_id == sample_to_compare.sample_id:
                continue
            distance: int = get_hamming_distance_index_2(
                sequence_1=sample.index2,
                sequence_2=sample_to_compare.index2,
                is_reverse_complement=is_run_reverse_complement,
            )
            if distance < MINIMUM_HAMMING_DISTANCE:
                return True
        return False

    @staticmethod
    def _get_samples_by_lane(
        samples: list[IlluminaSampleIndexSetting], lane: int
    ) -> list[IlluminaSampleIndexSetting]:
        """Return the samples of a given lane."""
        return [sample for sample in samples if sample.lane == lane]
