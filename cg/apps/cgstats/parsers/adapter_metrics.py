"""Parse statistics from the dragen adapter metrics file"""
import csv
import logging
from pathlib import Path
from typing import Dict, Tuple

LOG = logging.getLogger(__name__)


class AdapterMetrics:
    def __init__(self, adapter_metrics_path: Path):
        self.adapter_metrics_path = adapter_metrics_path
        self.parsed_metrics = self.parse_metrics_file()

    @staticmethod
    def summerize_adapter_metrics(parsed_metrics: Dict[int, dict]) -> Dict[Tuple[str, str], dict]:
        """Summerize forward and reverse read information for each sample in each lane."""

        summarized_metrics = {}
        for lane in parsed_metrics:
            # Iterate over all samples in lane
            summarized_metrics[lane] = summarized_metrics.get(lane, {})
            for value in parsed_metrics[lane].values():
                sample_id = value.get("Sample_ID")
                summarized_metrics[lane][sample_id] = summarized_metrics[lane].get(sample_id, value)
                summarized_metrics[lane][sample_id][
                    "R" + value.get("ReadNumber") + "_SampleBases"
                ] = value.get("SampleBases")

        return summarized_metrics

    def parse_metrics_file(self) -> Dict[int, dict]:
        """Parse the Dragen adapter metrics file."""
        LOG.info("Parsing Dragen demultiplexing adapter metrics file %s", self.adapter_metrics_path)
        parsed_metrics = {}

        with self.adapter_metrics_path.open("r") as metrics_file:
            metrics_reader = csv.DictReader(metrics_file)
            for row in metrics_reader:
                lane = int(row["Lane"])
                read_number = row["ReadNumber"]
                sample_id = row["Sample_ID"]
                parsed_metrics[lane] = parsed_metrics.get(lane, {})
                parsed_metrics[lane][(read_number, sample_id)] = row

        return self.summerize_adapter_metrics(parsed_metrics=parsed_metrics)
