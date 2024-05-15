"""This module parses metrics for files generated by the BCLConvert tool using the Dragen hardware."""
import logging
from pathlib import Path
from typing import Callable, Optional, Union

from cg.apps.demultiplex.sample_sheet.validators import is_valid_sample_internal_id
from cg.apps.sequencing_metrics_parser.models.bcl_convert import (
    BclConvertDemuxMetrics,
    BclConvertQualityMetrics,
)
from cg.constants.bcl_convert_metrics import (
    ADAPTER_METRICS_FILE_NAME,
    DEMUX_METRICS_FILE_NAME,
    QUALITY_METRICS_FILE_NAME,
)
from cg.constants.constants import SCALE_TO_READ_PAIRS, FileFormat
from cg.constants.demultiplexing import UNDETERMINED
from cg.io.controller import ReadFile
from cg.utils.files import get_file_in_directory

LOG = logging.getLogger(__name__)


class BclConvertMetricsParser:
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
        self.quality_metrics: list[BclConvertQualityMetrics] = self.parse_metrics_file(
            metrics_file_path=self.quality_metrics_path,
            metrics_model=BclConvertQualityMetrics,
        )
        self.demux_metrics: list[BclConvertDemuxMetrics] = self.parse_metrics_file(
            metrics_file_path=self.demux_metrics_path,
            metrics_model=BclConvertDemuxMetrics,
        )

    def parse_metrics_file(
        self, metrics_file_path, metrics_model: Callable
    ) -> list[Union[BclConvertQualityMetrics, BclConvertDemuxMetrics]]:
        """Parse specified BCL convert metrics file."""
        LOG.info(f"Parsing BCLConvert metrics file: {metrics_file_path}")
        parsed_metrics: list[Union[BclConvertQualityMetrics, BclConvertDemuxMetrics]] = []
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

    def get_metrics_for_sample_and_lane(
        self,
        metrics: list[Union[BclConvertQualityMetrics, BclConvertDemuxMetrics]],
        sample_internal_id: str,
        lane: int,
    ) -> Union[BclConvertQualityMetrics, BclConvertDemuxMetrics]:
        """Return the metrics for a sample by sample internal id."""
        for metric in metrics:
            if metric.sample_internal_id == sample_internal_id and metric.lane == lane:
                return metric

    def get_read_pair_metrics_for_sample_and_lane(
        self, sample_internal_id: str, lane: int
    ) -> list[BclConvertQualityMetrics]:
        """Return the read pair metrics for a sample and lane."""
        read_metrics: list[BclConvertQualityMetrics] = []
        for metric in self.quality_metrics:
            if metric.sample_internal_id == sample_internal_id and metric.lane == lane:
                read_metrics.append(metric)
        return read_metrics

    def calculate_total_reads_for_sample_in_lane(self, sample_internal_id: str, lane: int) -> int:
        """Calculate the total reads for a sample in a lane."""
        metric: BclConvertDemuxMetrics = self.get_metrics_for_sample_and_lane(
            metrics=self.demux_metrics, sample_internal_id=sample_internal_id, lane=lane
        )
        return metric.read_pair_count * SCALE_TO_READ_PAIRS

    def get_q30_bases_percent_for_sample_in_lane(self, sample_internal_id: str, lane: int) -> float:
        """Return the percent of bases that are Q30 for a sample and lane."""
        metrics: list[BclConvertQualityMetrics] = self.get_read_pair_metrics_for_sample_and_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )
        return self.calculate_mean_read_pair_q30_bases_percent(metrics=metrics)

    @classmethod
    def calculate_mean_read_pair_q30_bases_percent(
        cls, metrics: list[BclConvertQualityMetrics]
    ) -> float:
        """Calculate the percent of bases that are Q30 for read pairs."""
        mean_read_pair_q30_bases_percent: float = 0
        for metric in metrics:
            mean_read_pair_q30_bases_percent += metric.q30_bases_percent
        return round(mean_read_pair_q30_bases_percent / SCALE_TO_READ_PAIRS, 2) * 100

    @classmethod
    def calculate_mean_quality_score(cls, metrics: list[BclConvertQualityMetrics]) -> float:
        """Calculate the mean quality score for a list of metrics."""
        total_q_score: float = 0
        for metric in metrics:
            total_q_score += metric.mean_quality_score_q30
        return round(total_q_score / SCALE_TO_READ_PAIRS, 2)

    def get_mean_quality_score_for_sample_in_lane(
        self, sample_internal_id: str, lane: int
    ) -> float:
        """Return the mean quality score for a sample and lane."""
        metrics: list[BclConvertQualityMetrics] = self.get_read_pair_metrics_for_sample_and_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )
        return self.calculate_mean_quality_score(metrics=metrics)

    def has_undetermined_reads_in_lane(self, lane: int) -> bool:
        """Return whether there are undetermined reads in a lane."""
        metrics: Optional[BclConvertQualityMetrics] = self.get_metrics_for_sample_and_lane(
            metrics=self.quality_metrics, sample_internal_id=UNDETERMINED, lane=lane
        )
        return bool(metrics)