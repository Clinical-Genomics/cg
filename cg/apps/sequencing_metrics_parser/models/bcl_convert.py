from pydantic import BaseModel, BaseConfig, Field
import xml.etree.ElementTree as ET


class BclConvertQualityMetrics(BaseModel):
    """Model for the BCL Convert quality metrics"""

    lane: int
    sample_internal_id: str
    read_pair_number: int
    yield_bases: int
    yield_q30_bases: int
    quality_score_sum: int
    mean_quality_score_q30: float
    q30_bases_percent: float

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

    lane: int
    sample_internal_id: str
    sample_project: str
    read_pair_count: int
    perfect_index_reads_count: int
    perfect_index_reads_percent: float
    one_mismatch_index_reads_count: int
    two_mismatch_index_reads_count: int

    def _calculate_total_read_counts(self) -> int:
        """calculates the number of reads from reported number of read pairs"""
        return self.read_pair_count * 2


class BclConvertAdapterMetrics(BaseModel):
    """Model for the BCL Convert adapter metrics."""

    lane: int
    sample_internal_id: str
    sample_project: str
    read_number: int
    sample_bases: int

    def _calculate_sample_bases_for_read_pair(self) -> int:
        """calculates the total number of bases for a read pair."""
        pass


class BclConvertSampleSheet(BaseModel):
    """Model for the BCL Convert sample sheet."""

    flow_cell_name: str
    lane: int
    sample_internal_id: str
    sample_name: str
    control: str
    sample_project: str


class CustomConfig(BaseConfig):
    arbitrary_types_allowed = True


class BclConvertRunInfo(BaseModel):
    """Model for the BCL convert run info file."""

    tree: ET.ElementTree

    class Config(CustomConfig):
        pass

    def calculate_mean_read_length_from_run_info(self) -> int:
        """Get the mean read length for this flowcell"""
        read_lengths = [
            int(read.attrib["NumCycles"])
            for read in self.tree.findall("Run/Reads/Read")
            if read.attrib["IsIndexedRead"] == "N"
        ]
        return round(sum(read_lengths) / len(read_lengths), 0)
