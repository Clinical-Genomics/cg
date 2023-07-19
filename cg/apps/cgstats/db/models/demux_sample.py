import logging
from pydantic.v1 import BaseModel, validator

from cg.apps.cgstats.parsers.conversion_stats import SampleConversionResults
from cg.apps.cgstats.parsers.demux_stats import SampleBarcodeStats

LOG = logging.getLogger(__name__)


class DemuxSample(BaseModel):
    """Gather statistics from the demultiplexing results for a sample"""

    sample_name: str
    flowcell: str
    lane: int
    nr_raw_clusters_: int
    barcode_stats_: SampleBarcodeStats
    conversion_stats_: SampleConversionResults

    # derived fields etc
    raw_clusters_pc: float = 0.0
    pass_filter_yield_pc: float = 0.0
    pass_filter_clusters: int = 0
    pass_filter_yield: int = 0

    pass_filter_Q30: float = 0
    pass_filter_read1_q30: float = 0
    pass_filter_read2_q30: float = 0
    pass_filter_qscore: float = 0
    undetermined_pc: float = 0
    barcodes: int = 0
    perfect_barcodes: int = 0
    one_mismatch_barcodes: int = 0

    @validator("raw_clusters_pc", always=True)
    def set_raw_clusters_pc(cls, value: float, values: dict) -> float:
        """Calculate the percentage of raw clusters"""
        conversion_stats: SampleConversionResults = values["conversion_stats_"]
        if not values["nr_raw_clusters_"]:
            return value
        return round(conversion_stats.raw_cluster_count / values["nr_raw_clusters_"] * 100, 2)

    @validator("pass_filter_yield_pc", always=True)
    def set_pass_filter_yield_pc(cls, value: float, values: dict) -> float:
        """Calculate the pass filter yield percentage"""
        conversion_stats: SampleConversionResults = values["conversion_stats_"]
        if not values["conversion_stats_"].raw_yield:
            return value
        return round(
            conversion_stats.pass_filter_yield / conversion_stats.raw_yield * 100,
            2,
        )

    @validator("pass_filter_clusters", always=True)
    def set_pass_filter_clusters(cls, _, values) -> int:
        """Set the number of pass filter clusters"""
        conversion_stats: SampleConversionResults = values["conversion_stats_"]
        return conversion_stats.pass_filter_cluster_count

    @validator("pass_filter_yield", always=True)
    def set_pass_filter_yield(cls, _, values) -> int:
        """Set the number of pass filter yield (reads)"""
        conversion_stats: SampleConversionResults = values["conversion_stats_"]
        return conversion_stats.pass_filter_yield

    @validator("pass_filter_Q30", always=True)
    def set_pass_filter_Q30(cls, value, values) -> float:
        """Set the percentage of pass filter high quality reads"""
        conversion_stats: SampleConversionResults = values["conversion_stats_"]
        if not conversion_stats.pass_filter_yield:
            return value
        return round(conversion_stats.pass_filter_q30 / conversion_stats.pass_filter_yield * 100, 2)

    @validator("pass_filter_read1_q30", always=True)
    def set_percentage_high_quality_read_one(cls, value, values) -> float:
        """Calculate the percentage of high quality read one reads of all reads"""
        conversion_stats: SampleConversionResults = values["conversion_stats_"]
        if not conversion_stats.pass_filter_read1_yield:
            return value
        return round(
            conversion_stats.pass_filter_read1_q30 / conversion_stats.pass_filter_read1_yield * 100,
            2,
        )

    @validator("pass_filter_read2_q30", always=True)
    def set_percentage_high_quality_read_two(cls, value, values) -> float:
        """Calculate the percentage of high quality read two reads of all reads"""
        conversion_stats: SampleConversionResults = values["conversion_stats_"]
        if not conversion_stats.pass_filter_read2_yield:
            return value
        return round(
            conversion_stats.pass_filter_read2_q30 / conversion_stats.pass_filter_read2_yield * 100,
            2,
        )

    @validator("pass_filter_qscore", always=True)
    def set_pass_filter_qscore(cls, value, values) -> float:
        """Calculate the average quality score per read"""
        conversion_stats: SampleConversionResults = values["conversion_stats_"]
        if not conversion_stats.pass_filter_yield:
            return value
        return round(
            conversion_stats.pass_filter_quality_score_sum / conversion_stats.pass_filter_yield,
            2,
        )

    @validator("undetermined_pc", always=True)
    def set_undetermined_pc(cls, value, values) -> float:
        """Calculate the average quality score per read"""
        conversion_stats: SampleConversionResults = values["conversion_stats_"]
        barcode_stats: SampleBarcodeStats = values["barcode_stats_"]
        if not conversion_stats.pass_filter_cluster_count:
            return value
        return round(
            (conversion_stats.pass_filter_cluster_count - barcode_stats.barcode_count)
            / conversion_stats.pass_filter_cluster_count
            * 100,
            2,
        )

    @validator("barcodes", always=True)
    def set_nr_barcodes(cls, _, values) -> int:
        """Set the total number of barcodes"""
        barcode_stats: SampleBarcodeStats = values["barcode_stats_"]
        return barcode_stats.barcode_count or 0

    @validator("perfect_barcodes", always=True)
    def set_nr_perfect_barcodes(cls, _, values) -> int:
        """Set the total number of perfect barcodes"""
        barcode_stats: SampleBarcodeStats = values["barcode_stats_"]
        return barcode_stats.perfect_barcode_count or 0

    @validator("one_mismatch_barcodes", always=True)
    def set_nr_one_mismatch_barcodes(cls, _, values) -> int:
        """Set the total number of mismatch barcodes"""
        barcode_stats: SampleBarcodeStats = values["barcode_stats_"]
        return barcode_stats.one_mismatch_barcode_count or 0
