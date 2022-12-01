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
                read_number = row["ReadNumber"]
                sample_id = row["SampleID"]
                parsed_metrics[lane] = parsed_metrics.get(lane, {})
                row["YieldQ30"] = int(row["YieldQ30"])
                parsed_metrics[lane][(read_number, sample_id)] = row

        return self.summerize_quality_metrics(parsed_metrics=parsed_metrics)

    @staticmethod
    def summerize_quality_metrics(parsed_metrics: Dict[int, dict]) -> Dict[Tuple[str, str], dict]:
        """Summerize forward and reverse read information for each sample in each lane."""

        summarized_metrics = {}
        for lane in parsed_metrics:
            # Iterate over all samples in lane
            summarized_metrics[lane] = summarized_metrics.get(lane, {})
            for value in parsed_metrics[lane].values():
                value["YieldQ30"] = int(value["YieldQ30"])
                value["Mean Quality Score (PF)"] = float(value["Mean Quality Score (PF)"])
                value["QualityScoreSum"] = int(value["QualityScoreSum"])
                sample_id = value.get("SampleID")
                if sample_id not in summarized_metrics[lane]:
                    summarized_metrics[lane][sample_id] = value
                    continue
                summarized_metrics[lane][sample_id]["YieldQ30"] += value.get("YieldQ30")
                summarized_metrics[lane][sample_id]["Mean Quality Score (PF)"] += value.get(
                    "Mean Quality Score (PF)"
                )
                summarized_metrics[lane][sample_id]["QualityScoreSum"] += value.get(
                    "QualityScoreSum"
                )

        return summarized_metrics
