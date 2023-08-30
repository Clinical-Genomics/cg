"""Parse Dragen demultiplexing statistics from Demultiplex_Stats.csv """
import csv
import logging
from pathlib import Path
from typing import Dict

from pydantic.v1 import BaseModel

LOG = logging.getLogger(__name__)


class SampleConversionResults(BaseModel):
    """Class to collect the Dragen demultiplexing conversion results for a sample on a lane"""

    raw_cluster_count: int = 0
    raw_yield: int = 0
    pass_filter_cluster_count: int = 0
    pass_filter_read1_yield: int = 0
    pass_filter_read2_yield: int = 0
    pass_filter_yield: int = 0
    pass_filter_q30: int = 0
    pass_filter_read1_q30: int = 0
    pass_filter_read2_q30: int = 0
    pass_filter_quality_score_sum: int = 0
    pass_filter_quality_score: float = 0
    barcode: str = ""
    sample_id: str = ""


class DragenDemultiplexingStats:
    def __init__(self, demux_stats_path: Path):
        self.demux_stats_path = demux_stats_path
        self.parsed_stats: Dict[int, dict] = self.parse_stats_file()

    def parse_stats_file(
        self,
    ) -> Dict[int, dict]:
        """Parse the Dragen demultiplexing stats file"""
        LOG.info("Parsing Dragen demultiplexing stats file %s", self.demux_stats_path)

        parsed_stats = {}

        with open(self.demux_stats_path, mode="r") as stats_file:
            stats_reader = csv.DictReader(stats_file)
            for row in stats_reader:
                lane = int(row["Lane"])
                sample_id = row["SampleID"]
                parsed_stats[lane] = parsed_stats.get(lane, {})
                parsed_stats[lane][sample_id] = row

        return parsed_stats
