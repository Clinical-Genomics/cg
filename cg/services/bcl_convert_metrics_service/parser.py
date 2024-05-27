"""This module parses metrics for files generated by the BCL converter and demultiplexing."""

import logging
from pathlib import Path
from typing import Callable

from cg.apps.demultiplex.sample_sheet.validators import is_valid_sample_internal_id

from cg.constants.constants import SCALE_TO_READ_PAIRS, FileFormat
from cg.constants.demultiplexing import UNDETERMINED
from cg.constants.metrics import (
    ADAPTER_METRICS_FILE_NAME,
    DEMUX_METRICS_FILE_NAME,
    QUALITY_METRICS_FILE_NAME,
)
from cg.io.controller import ReadFile
from cg.services.bcl_convert_metrics_service.models import DemuxMetrics, SequencingQualityMetrics
from cg.utils.files import get_file_in_directory

LOG = logging.getLogger(__name__)


class MetricsParser:
    def __init__(
        self,
        bcl_convert_metrics_dir_path: Path,
    ) -> None:
        """Initialize the class."""
        self.bcl_convert_demultiplex_dir: Path = bcl_convert_metrics_dir_path
        self.quality_metrics_path: Path = get_file_in_directory(
            directory=self.bcl_convert_demultiplex_dir, file_name=QUALITY_METRICS_FILE_NAME
        )
        self.demux_metrics_path: Path = get_file_in_directory(
            directory=self.bcl_convert_demultiplex_dir, file_name=DEMUX_METRICS_FILE_NAME
        )
        self.adapter_metrics_path: Path = get_file_in_directory(
            directory=self.bcl_convert_demultiplex_dir, file_name=ADAPTER_METRICS_FILE_NAME
        )
        self.quality_metrics: list[SequencingQualityMetrics] = self.parse_metrics_file(
            metrics_file_path=self.quality_metrics_path,
            metrics_model=SequencingQualityMetrics,
        )
        self.demux_metrics: list[DemuxMetrics] = self.parse_metrics_file(
            metrics_file_path=self.demux_metrics_path,
            metrics_model=DemuxMetrics,
        )

    @staticmethod
    def parse_metrics_file(
        metrics_file_path, metrics_model: Callable
    ) -> list[SequencingQualityMetrics | DemuxMetrics]:
        """Parse specified metrics file."""
        LOG.info(f"Parsing BCLConvert metrics file: {metrics_file_path}")
        parsed_metrics: list[SequencingQualityMetrics | DemuxMetrics] = []
        metrics_content: list[dict] = ReadFile.get_content_from_file(
            file_format=FileFormat.CSV, file_path=metrics_file_path, read_to_dict=True
        )
        for sample_metrics_dict in metrics_content:
            parsed_metrics.append(metrics_model(**sample_metrics_dict))
        return parsed_metrics

    def get_sample_internal_ids(self) -> list[str]:
        """Return a list of sample internal ids."""
        sample_internal_ids: list[str] = []
        for sample_demux_metric in self.demux_metrics:
            if is_valid_sample_internal_id(
                sample_internal_id=sample_demux_metric.sample_internal_id
            ):
                sample_internal_ids.append(sample_demux_metric.sample_internal_id)
        return list(set(sample_internal_ids))

    def get_lanes_for_sample(self, sample_internal_id: str) -> list[int]:
        """Return a list of lanes for a sample."""
        lanes_for_sample: list[int] = []
        for sample_demux_metric in self.demux_metrics:
            if sample_demux_metric.sample_internal_id == sample_internal_id:
                lanes_for_sample.append(sample_demux_metric.lane)
        return lanes_for_sample

    @staticmethod
    def get_metrics_for_sample_and_lane(
        metrics: list[SequencingQualityMetrics | DemuxMetrics],
        sample_internal_id: str,
        lane: int,
    ) -> SequencingQualityMetrics | DemuxMetrics:
        """Return the metrics for a sample by sample internal id."""
        for metric in metrics:
            if metric.sample_internal_id == sample_internal_id and metric.lane == lane:
                return metric

    def get_read_pair_metrics_for_sample_and_lane(
        self, sample_internal_id: str, lane: int
    ) -> list[SequencingQualityMetrics]:
        """Return the read pair metrics for a sample and lane."""
        read_metrics: list[SequencingQualityMetrics] = []
        for metric in self.quality_metrics:
            if metric.sample_internal_id == sample_internal_id and metric.lane == lane:
                read_metrics.append(metric)
        return read_metrics

    def calculate_total_reads_for_sample_in_lane(self, sample_internal_id: str, lane: int) -> int:
        """Calculate the total reads for a sample in a lane."""
        metric: DemuxMetrics = self.get_metrics_for_sample_and_lane(
            metrics=self.demux_metrics, sample_internal_id=sample_internal_id, lane=lane
        )
        return metric.read_pair_count * SCALE_TO_READ_PAIRS

    def get_q30_bases_percent_for_sample_in_lane(self, sample_internal_id: str, lane: int) -> float:
        """Return the percent of bases that are Q30 for a sample and lane."""
        metrics: list[SequencingQualityMetrics] = self.get_read_pair_metrics_for_sample_and_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )
        return self.calculate_mean_read_pair_q30_bases_percent(metrics=metrics)

    def get_yield_for_sample_in_lane(self, sample_internal_id: str, lane: int) -> int:
        """Return the yield for a sample and lane."""
        metrics: list[SequencingQualityMetrics] = self.get_read_pair_metrics_for_sample_and_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )
        return self.sum_yield(metrics=metrics)

    def get_yield_q30_for_sample_in_lane(self, sample_internal_id: str, lane: int) -> int:
        """Return the yield Q30 for a sample and lane."""
        metrics: list[SequencingQualityMetrics] = self.get_read_pair_metrics_for_sample_and_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )
        return self.sum_yield_q30(metrics=metrics)

    @classmethod
    def calculate_mean_read_pair_q30_bases_percent(
        cls, metrics: list[SequencingQualityMetrics]
    ) -> float:
        """Calculate the percent of bases that are Q30 for read pairs."""
        mean_read_pair_q30_bases_percent: float = 0
        for metric in metrics:
            mean_read_pair_q30_bases_percent += metric.q30_bases_percent
        return round(mean_read_pair_q30_bases_percent / SCALE_TO_READ_PAIRS, 2) * 100

    @classmethod
    def calculate_mean_quality_score(cls, metrics: list[SequencingQualityMetrics]) -> float:
        """Calculate the mean quality score for a list of metrics."""
        total_q_score: float = 0
        for metric in metrics:
            total_q_score += metric.mean_quality_score_q30
        return round(total_q_score / SCALE_TO_READ_PAIRS, 2)

    def sum_yield(self, metrics: list[SequencingQualityMetrics]) -> int:
        """Calculate the mean yield for a list of metrics."""
        return self.get_aggregate_for_attribute(metrics=metrics, attr_name="yield_")

    def sum_yield_q30(self, metrics: list[SequencingQualityMetrics]) -> int:
        """Calculate the mean yield Q30 for a list of metrics."""
        return self.get_aggregate_for_attribute(metrics=metrics, attr_name="yield_q30")

    def get_mean_quality_score_for_sample_in_lane(
        self, sample_internal_id: str, lane: int
    ) -> float:
        """Return the mean quality score for a sample and lane."""
        metrics: list[SequencingQualityMetrics] = self.get_read_pair_metrics_for_sample_and_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )
        return self.calculate_mean_quality_score(metrics=metrics)

    def has_undetermined_reads_in_lane(self, lane: int) -> bool:
        """Return whether there are undetermined reads in a lane."""
        metrics: SequencingQualityMetrics | None = self.get_metrics_for_sample_and_lane(
            metrics=self.quality_metrics, sample_internal_id=UNDETERMINED, lane=lane
        )
        return bool(metrics)

    @classmethod
    def calculate_total_reads_for_metrics(cls, read_pair_count: int) -> int:
        """Scale to read pair number up to single reads."""
        return read_pair_count * SCALE_TO_READ_PAIRS

    def get_total_reads_for_flow_cell(self):
        """Return the aggregate reads for the whole demux metrics."""
        aggregate_read_pairs: int = self.get_aggregate_for_attribute(
            metrics=self.demux_metrics, attr_name="read_pair_count"
        )
        return self.calculate_total_reads_for_metrics(read_pair_count=aggregate_read_pairs)

    def get_undetermined_reads_for_flow_cell(self) -> int:
        """Calculate the total undetermined reads to the demux metrics."""
        aggregate_undetermined_read_pairs: int = 0
        for demux_metric in self.demux_metrics:
            if demux_metric.sample_internal_id == UNDETERMINED:
                aggregate_undetermined_read_pairs += demux_metric.read_pair_count
        return self.calculate_total_reads_for_metrics(
            read_pair_count=aggregate_undetermined_read_pairs
        )

    def get_mean_percent_q30_for_flow_cell(self) -> float:
        """Calculate the mean percent Q30 for the aggregated quality metrics."""
        aggregate_yield: int = self.get_yield_for_flow_cell()
        aggregate_yield_q30: int = self.get_yield_q30_for_flow_cell()
        return round(aggregate_yield_q30 / aggregate_yield, 2)

    def get_mean_quality_score_sum_for_flow_cell(self) -> float:
        """Calculate the mean quality score for the aggregated quality metrics."""
        aggregate_quality_score: int = self.get_aggregate_for_attribute(
            self.quality_metrics, "quality_score_sum"
        )
        aggregate_yield: int = self.get_yield_for_flow_cell()
        return round(aggregate_quality_score / aggregate_yield, 2)

    def get_yield_for_flow_cell(self) -> int:
        """Calculate the aggregate yield for the quality metrics."""
        return self.get_aggregate_for_attribute(metrics=self.quality_metrics, attr_name="yield_")

    def get_yield_q30_for_flow_cell(self) -> int:
        """Calculate the aggregate yield Q30 for the quality metrics."""
        return self.get_aggregate_for_attribute(metrics=self.quality_metrics, attr_name="yield_q30")

    @staticmethod
    def get_aggregate_for_attribute(metrics: list, attr_name: str) -> int:
        """Calculate the aggregate sum of a specified attribute for a given list of objects."""
        aggregate_value: int = 0
        for metric in metrics:
            aggregate_value += getattr(metric, attr_name)
        return aggregate_value
