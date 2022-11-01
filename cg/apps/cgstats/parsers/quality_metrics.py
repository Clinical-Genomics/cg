"""Parse statistics from the dragen quality metrics file"""
import csv
import logging
from pathlib import Path
from typing import Dict

LOG = logging.getLogger(__name__)


class QualityMetrics:
    def __init__(self, quality_metrics_path: Path):
        self.quality_metrics_path = quality_metrics_path
        self.parsed_metrics = self.parse_metrics_file()

    def parse_metrics_file(
        self,
    ) -> Dict[int, dict]:
        """Parse the Dragen quality metrics file"""
        LOG.info("Parsing Dragen demultiplexing quality metrics file %s", self.quality_metrics_path)

        parsed_metrics = {}

        with open(self.quality_metrics_path, mode="r") as metrics_file:
            metrics_reader = csv.DictReader(metrics_file)
            for row in metrics_reader:
                lane = int(row["Lane"])
                sample_id = row["Sample_ID"]
                parsed_metrics[lane] = parsed_metrics.get(lane, {})
                parsed_metrics[lane][sample_id] = row

        return parsed_metrics

