from pydantic import BaseModel
import xml.etree.ElementTree as ET


class BclConvertQualityMetrics(BaseModel):
    """Model for the BCL Convert quality metrics"""

    def __init__(
        self,
        lane: int,
        sample_internal_id: str,
        read_pair_number: int,
        yield_bases: int,
        yield_q30_bases: int,
        quality_score_sum: int,
        mean_quality_score_q30: float,
        q30_bases_percent: float,
    ):
        self.lane = lane
        self.sample_internal_id = sample_internal_id
        self.read_pair_number = read_pair_number
        self.yield_bases = yield_bases
        self.yield_q30_bases = yield_q30_bases
        self.quality_score_sum = quality_score_sum
        self.mean_quality_score_q30 = mean_quality_score_q30
        self.percent_q30 = q30_bases_percent

    def get_read_pair_summarised_yield(self) -> int:
        """Summarise the yield for the read pair"""
        pass

    def _get_read_pair_summarised_yield_q30(self) -> int:
        """Summarise the yield passing q30 for the read pair"""
        pass

    def _get_read_pair_summarised_quality_score_sum(self) -> int:
        """Summarise the yield for the read pair"""
        pass

    def _get_read_pair_summarised_mean_quality_score_q30(self) -> int:
        """Summarise the yield for the read pair"""
        pass

    def _get_read_pair_summarised_percent_q30(self) -> int:
        """Summarise the yield for the read pair"""
        pass


class BclConvertDemuxMetrics(BaseModel):
    """Model for the BCL Convert demultiplexing metrics."""

    def __init__(
        self,
        lane: int,
        sample_internal_id: str,
        sample_project: str,
        read_pair_count: int,
        perfect_index_reads_count: int,
        perfect_index_reads_percent: float,
        one_mismatch_index_reads_count: int,
        two_mismatch_index_reads_count: int,
    ):

        self.sample_internal_id = sample_internal_id
        self.lane = lane
        self.sample_project = sample_project
        self.read_pairs = read_pair_count
        self.perfect_index_reads = perfect_index_reads_count
        self.perfect_index_reads_percent = perfect_index_reads_percent
        self.one_mismatch_reads = one_mismatch_index_reads_count
        self.two_mismatch_reads = two_mismatch_index_reads_count

    def _calculate_total_read_counts(self) -> int:
        """calculates the number of reads from reported number of read pairs"""
        return self.read_pairs * 2


class BclConvertAdapterMetrics(BaseModel):
    """Model for the BCL Convert adapter metrics."""

    def __init__(
        self,
        lane: int,
        sample_internal_id: str,
        sample_project: str,
        read_number: int,
        sample_bases: int,
    ):

        self.lane = lane
        self.sample_internal_id = sample_internal_id
        self.sample_project = sample_project
        self.read_number = read_number
        self.sample_bases = sample_bases

    def _calculate_sample_bases_for_read_pair(self) -> int:
        """calculates the total number of bases for a read pair."""
        pass


class BclConvertSampleSheet(BaseModel):
    """Model for the BCL Convert sample sheet."""

    def __init__(
        self,
        flow_cell_name: str,
        lane: int,
        sample_internal_id: str,
        sample_name: str,
        control: str,
        sample_project: str,
    ):

        self.flow_cell_name = flow_cell_name
        self.lane = lane
        self.sample_internal_id = sample_internal_id
        self.sample_name = sample_name
        self.control = control
        self.sample_project = sample_project


class BclConvertRunInfo(BaseModel):
    """Model for the BCL convert run info file."""

    def __init__(self, tree: ET.Element):
        self.tree = tree

    def calculate_mean_read_length_from_run_info(self) -> int:
        """Get the mean read length for this flowcell"""
        read_lengths = [
            int(read.attrib["NumCycles"])
            for read in self.tree.findall("Run/Reads/Read")
            if read.attrib["IsIndexedRead"] == "N"
        ]
        return round(sum(read_lengths) / len(read_lengths), 0)
