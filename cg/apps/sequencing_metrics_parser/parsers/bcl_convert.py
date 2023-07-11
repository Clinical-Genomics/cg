"""This module parses metrics for files generated by the BCLConvert tool using the Dragen hardware."""
import csv
import re
import logging
from pathlib import Path
from typing import List, Union, Dict, Callable
from cg.io.controller import ReadFile
from cg.constants.demultiplexing import SampleSheetNovaSeq6000Sections
from cg.constants.constants import FileFormat, SCALE_TO_READ_PAIRS
from cg.constants.bcl_convert_metrics import (
    DEMUX_METRICS_FILE_NAME,
    QUALITY_METRICS_FILE_NAME,
    ADAPTER_METRICS_FILE_NAME,
    SAMPLE_SHEET_FILE_NAME,
)
from cg.apps.sequencing_metrics_parser.models.bcl_convert import (
    BclConvertAdapterMetrics,
    BclConvertDemuxMetrics,
    BclConvertQualityMetrics,
    BclConvertSampleSheetData,
)
from cg.constants.demultiplexing import INDEX_CHECK, UNDETERMINED
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
        self.sample_sheet_path: Path = get_file_in_directory(
            directory=self.bcl_convert_demultiplex_dir, file_name=SAMPLE_SHEET_FILE_NAME
        )
        self.quality_metrics: List[BclConvertQualityMetrics] = self.parse_metrics_file(
            metrics_file_path=self.quality_metrics_path,
            metrics_model=BclConvertQualityMetrics,
        )
        self.demux_metrics: List[BclConvertDemuxMetrics] = self.parse_metrics_file(
            metrics_file_path=self.demux_metrics_path,
            metrics_model=BclConvertDemuxMetrics,
        )
        self.adapter_metrics: List[BclConvertAdapterMetrics] = self.parse_metrics_file(
            self.adapter_metrics_path,
            metrics_model=BclConvertAdapterMetrics,
        )
        self.sample_sheet: List[BclConvertSampleSheetData] = self.parse_sample_sheet_file(
            sample_sheet_path=self.sample_sheet_path
        )

    def parse_metrics_file(
        self, metrics_file_path, metrics_model: Callable
    ) -> List[Union[BclConvertQualityMetrics, BclConvertDemuxMetrics, BclConvertAdapterMetrics]]:
        """Parse specified BCL convert metrics file."""
        if not metrics_file_path.exists():
            raise FileNotFoundError(f"File {metrics_file_path} does not exist.")
        LOG.info(f"Parsing BCLConvert metrics file: {metrics_file_path}")
        parsed_metrics: List[
            Union[BclConvertQualityMetrics, BclConvertDemuxMetrics, BclConvertAdapterMetrics]
        ] = []
        metrics_content: List[Dict] = ReadFile.get_content_from_file(
            file_format=FileFormat.CSV, file_path=metrics_file_path, read_to_dict=True
        )
        for sample_metrics_dict in metrics_content:
            parsed_metrics.append(metrics_model(**sample_metrics_dict))
        return parsed_metrics

    def get_nr_of_header_lines_in_sample_sheet(self, sample_sheet_path: Path) -> int:
        """Return the number of header lines in a sample sheet.
        Any lines before and including the line starting with [Data] is considered the header."""
        sample_sheet_content = ReadFile.get_content_from_file(FileFormat.CSV, sample_sheet_path)
        header_line_count: int = 1
        for line in sample_sheet_content:
            if SampleSheetNovaSeq6000Sections.Data.HEADER.value in line:
                break
            header_line_count += 1
        return header_line_count

    def parse_sample_sheet_file(self, sample_sheet_path: Path) -> List[BclConvertSampleSheetData]:
        """Return sample sheet sample lines."""
        LOG.info(f"Parsing BCLConvert sample sheet file: {sample_sheet_path}")
        header_line_count: int = self.get_nr_of_header_lines_in_sample_sheet(
            sample_sheet_path=sample_sheet_path
        )
        sample_sheet_sample_lines: List[BclConvertSampleSheetData] = []
        with open(sample_sheet_path, "r") as sample_sheet_file:
            for _ in range(header_line_count):
                next(sample_sheet_file)
            sample_sheet_content = csv.DictReader(sample_sheet_file)
            for line in sample_sheet_content:
                sample_sheet_sample_lines.append(BclConvertSampleSheetData(**line))
        return sample_sheet_sample_lines

    def get_sample_internal_ids(self) -> List[str]:
        """Return a list of sample internal ids."""
        sample_internal_ids: List[str] = []
        for sample_demux_metric in self.demux_metrics:
            if self.is_valid_sample(sample_internal_id=sample_demux_metric.sample_internal_id):
                sample_internal_ids.append(sample_demux_metric.sample_internal_id)
        return list(set(sample_internal_ids))

    def is_valid_sample(self, sample_internal_id: str) -> bool:
        """Return True if the sample project is valid."""
        pattern = r"^[A-Za-z]{3}[0-9]{3}.*"
        if re.match(pattern, sample_internal_id) is not None:
            return True
        return False

    def get_lanes_for_sample(self, sample_internal_id: str) -> List[int]:
        """Return a list of lanes for a sample."""
        lanes_for_sample: List[int] = []
        for sample_demux_metric in self.demux_metrics:
            if sample_demux_metric.sample_internal_id == sample_internal_id:
                lanes_for_sample.append(sample_demux_metric.lane)
        return lanes_for_sample

    def get_metrics_for_sample_and_lane(
        self,
        metrics: List[
            Union[BclConvertQualityMetrics, BclConvertDemuxMetrics, BclConvertAdapterMetrics]
        ],
        sample_internal_id: str,
        lane: int,
    ) -> Union[BclConvertQualityMetrics, BclConvertDemuxMetrics, BclConvertAdapterMetrics]:
        """Return the metrics for a sample by sample internal id."""
        for metric in metrics:
            if metric.sample_internal_id == sample_internal_id and metric.lane == lane:
                return metric

    def get_read_pair_metrics_for_sample_and_lane(
        self, sample_internal_id: str, lane: int
    ) -> List[BclConvertQualityMetrics]:
        """Return the read pair metrics for a sample and lane."""
        read_metrics: List[BclConvertQualityMetrics] = []
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

    def get_flow_cell_name(self) -> str:
        """Return the flow cell name of the demultiplexed flow cell."""
        return self.sample_sheet[0].flow_cell_name

    def get_q30_bases_percent_for_sample_in_lane(self, sample_internal_id: str, lane: int) -> float:
        """Return the percent of bases that are Q30 for a sample and lane."""
        metrics: List[BclConvertQualityMetrics] = self.get_read_pair_metrics_for_sample_and_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )
        return self.calculate_mean_read_pair_q30_bases_percent(metrics=metrics)

    @classmethod
    def calculate_mean_read_pair_q30_bases_percent(
        cls, metrics: List[BclConvertQualityMetrics]
    ) -> float:
        """Calculate the percent of bases that are Q30 for read pairs."""
        mean_read_pair_q30_bases_percent: float = 0
        for metric in metrics:
            mean_read_pair_q30_bases_percent += metric.q30_bases_percent
        return round(mean_read_pair_q30_bases_percent / SCALE_TO_READ_PAIRS, 2)

    @classmethod
    def calculate_mean_quality_score(cls, metrics: List[BclConvertQualityMetrics]) -> float:
        """Calculate the mean quality score for a list of metrics."""
        total_q_score: float = 0
        for metric in metrics:
            total_q_score += metric.mean_quality_score_q30
        return round(total_q_score / SCALE_TO_READ_PAIRS, 2)

    def get_mean_quality_score_for_sample_in_lane(
        self, sample_internal_id: str, lane: int
    ) -> float:
        """Return the mean quality score for a sample and lane."""
        metrics: List[BclConvertQualityMetrics] = self.get_read_pair_metrics_for_sample_and_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )
        return self.calculate_mean_quality_score(metrics=metrics)
