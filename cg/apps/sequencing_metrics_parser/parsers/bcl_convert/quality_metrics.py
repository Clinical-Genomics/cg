"""Parse the quality metrics file from BCL convert into a pydantic model."""

from pydantic import BaseModel
from cg.apps.sequencing_metrics_parser.models.bcl_convert.quality_metrics import QualityMetrics
from typing import Dict, Tuple, List
from pathlib import Path
import logging

LOG = logging.getLogger(__name__)


class BclConvertQualityMetrics(BaseModel):
    def __init__(self, bcl_convert_quality_metrics_path: Path):
        self.metrics_path: Path = bcl_convert_quality_metrics_path
        self.parsed_metrics: List[QualityMetrics] = self.parse_quality_metrics_file()

    def parse_quality_metrics_file(
        self,
    ) -> List[QualityMetrics]:
        """Parse the BCL convert metrics file with read pair format into a dictionary."""
        LOG.info(f"Parsing BCLConvert metrics file: {self.metrics_path}")
        parsed_metrics: List[QualityMetrics] = []
        with open(self.metrics_path, mode="r") as metrics_file:
            metrics_reader = csv.DictReader(metrics_file)
            for row in metrics_reader:
                parsed_metrics.append(
                    QualityMetrics(
                        lane=int(row["Lane"]),
                        sample_internal_id=row["SampleID"],
                        read_pair_number=row["ReadNumber"],
                        yield_bases=int(row["Yield"]),
                        yield_q30=int(row["YieldQ30"]),
                        quality_score_sum=int(row["QualityScoreSum"]),
                        mean_quality_score=float(row["Mean Quality Score (PF)"]),
                        q30_bases_percent=float(row["% Q30"]),
                    )
                )
        return parsed_metrics

    def summerize_quality_metrics(
        self, parsed_metrics: Dict[int, dict]
    ) -> Dict[Tuple[str, str], dict]:
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
