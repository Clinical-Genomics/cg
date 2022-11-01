"""Parse statistics from the dragen quality metrics file"""
import csv
import logging
from pathlib import Path
from typing import Dict, Tuple

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
                sample_id = row["SampleID"]
                parsed_metrics[lane] = parsed_metrics.get(lane, {})
                parsed_metrics[lane][sample_id] = row

        return self.summerize_quality_metrics(parsed_metrics=parsed_metrics)

    @staticmethod
    def summerize_quality_metrics(parsed_metrics: Dict[int, dict]) -> Dict[Tuple[str, str], dict]:
        """Summerize forward and reverse read information for each sample in each lane."""

        summarized_metrics = {}
        for lane in parsed_metrics:
            # Iterate over all samples in lane
            summarized_metrics[lane] = summarized_metrics.get(lane, {})
            for value in parsed_metrics[lane].values():
                sample_id = value.get("Sample_ID")
                summarized_metrics[lane][sample_id] = summarized_metrics[lane].get(sample_id, value)
                summarized_metrics[lane][sample_id]["YieldQ30"] += int(value.get("YieldQ30"))

        return summarized_metrics
