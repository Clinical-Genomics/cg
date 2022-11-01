"""Parse statistics from the dragen adapter metrics file"""
import csv
import logging
from pathlib import Path
from typing import Dict

LOG = logging.getLogger(__name__)


class AdapterMetrics:
    def __init__(self, adapter_metrics_path: Path):
        self.adapter_metrics_path = adapter_metrics_path
        self.parsed_metrics = self.parse_metrics_file()

    def parse_metrics_file(
        self,
    ) -> Dict[int, dict]:
        """Parse the Dragen adapter metrics file"""
        LOG.info("Parsing Dragen demultiplexing adapter metrics file %s", self.adapter_metrics_path)

        parsed_metrics = {}

        with open(self.adapter_metrics_path, mode="r") as metrics_file:
            metrics_reader = csv.DictReader(metrics_file)
            for row in metrics_reader:
                lane = int(row["Lane"])
                sample_id = row["Sample_ID"]
                parsed_metrics[lane] = parsed_metrics.get(lane, {})
                parsed_metrics[lane][sample_id] = row

        summerized_metrics = self.summerize_adapter_metrics(parsed_metrics)

        return summerized_metrics

    def summerize_adapter_metrics(self, parsed_metrics: Dict[int, dict]) -> Dict[int, dict]:
        """Summerize lane information for each sample"""

        summerized_metrics = parsed_metrics

        for lane in summerized_metrics.items():
            # iterate through the sample dict in second tuple index
            for value in lane[1].values():
                value["R1_SampleBases"] = value["SampleBases"]
                value["R2_SampleBases"] = value["SampleBases"]
                del value["SampleBases"]

        return summerized_metrics
