"""This module parses metrics for files generated by the BCLConvert tool using the dragen hardware."""
import csv
import xml.etree.ElementTree as ET
import logging
from pathlib import Path
from typing import List

from cg.constants.demultiplexing import SampleSheetHeaderColumnNames

from cg.apps.sequencing_metrics_parser.models.bcl_convert import (
    BclConvertAdapterMetrics,
    BclConvertDemuxMetrics,
    BclConvertQualityMetrics,
    BclConvertRunInfo,
    BclConvertSampleSheet,
)


LOG = logging.getLogger(__name__)


class BclConvertMetricsParser:
    def __init__(
        self,
        bcl_convert_quality_metrics_path: Path,
        bcl_convert_demux_metrics_file_path: Path,
        bcl_convert_adapter_metrics_file_path: Path,
        bcl_convert_sample_sheet_file_path: Path,
        bcl_convert_run_info_file_path: Path,
    ) -> None:
        """Initialize the class."""
        self.quality_metrics_path: Path = bcl_convert_quality_metrics_path
        self.demux_metrics_path: Path = bcl_convert_demux_metrics_file_path
        self.adapter_metrics_path: Path = bcl_convert_adapter_metrics_file_path
        self.sample_sheet_path: Path = bcl_convert_sample_sheet_file_path
        self.run_info_path: Path = bcl_convert_run_info_file_path
        self.quality_metrics: List[BclConvertQualityMetrics] = self.parse_quality_metrics_file()
        self.demux_metrics: List[BclConvertDemuxMetrics] = self.parse_demux_metrics_file()
        self.adapter_metrics: List[BclConvertAdapterMetrics] = self.parse_adapter_metrics_file()
        self.sample_sheet: List[BclConvertSampleSheet] = self.parse_sample_sheet_file()
        self.run_info: BclConvertRunInfo = self.parse_run_info_file()

    def parse_quality_metrics_file(
        self,
    ) -> List[BclConvertQualityMetrics]:
        """Parse the BCL convert metrics file with read pair format into a BclConvertQualityMetrics model."""
        LOG.info(f"Parsing BCLConvert metrics file: {self.quality_metrics_path}")
        parsed_metrics: List[BclConvertQualityMetrics] = []
        with open(self.quality_metrics_path, mode="r") as metrics_file:
            metrics_reader = csv.DictReader(metrics_file)
            for row in metrics_reader:
                parsed_metrics.append(
                    BclConvertQualityMetrics(
                        lane=int(row["Lane"]),
                        sample_internal_id=row["SampleID"],
                        read_pair_number=row["ReadNumber"],
                        yield_bases=int(row["Yield"]),
                        yield_q30_bases=int(row["YieldQ30"]),
                        quality_score_sum=int(row["QualityScoreSum"]),
                        mean_quality_score_q30=float(row["Mean Quality Score (PF)"]),
                        q30_bases_percent=float(row["% Q30"]),
                    )
                )
        return parsed_metrics

    def parse_demux_metrics_file(self) -> List[BclConvertDemuxMetrics]:
        """Reads a BCL convert demux metrics file into the BclConvertDemuxMetrics model."""
        LOG.info(f"Parsing BCLConvert metrics file: {self.demux_metrics_path}")
        parsed_metrics = []
        with open(self.demux_metrics_path, mode="r") as stats_file:
            stats_reader = csv.DictReader(stats_file)
            for row in stats_reader:
                parsed_metrics.append(
                    BclConvertDemuxMetrics(
                        lane=int(row["Lane"]),
                        sample_internal_id=row["SampleID"],
                        sample_project=row["Sample_Project"],
                        read_pair_count=row["# Reads"],
                        perfect_index_reads_count=row["# Perfect Index Reads"],
                        perfect_index_reads_percent=row["% Perfect Index Reads"],
                        one_mismatch_index_reads_count=row["# One Mismatch Index Reads"],
                        two_mismatch_index_reads_count=row["# Two Mismatch Index Reads"],
                    )
                )
            return parsed_metrics

    def parse_adapter_metrics_file(self) -> List[BclConvertAdapterMetrics]:
        LOG.info(f"Parsing BCL convert adapter metrics file {self.adapter_metrics_path}")
        parsed_metrics: List[BclConvertAdapterMetrics] = []
        with self.adapter_metrics_path.open("r") as metrics_file:
            metrics_reader = csv.DictReader(metrics_file)
            for row in metrics_reader:
                parsed_metrics.append(
                    BclConvertAdapterMetrics(
                        lane=int(row["Lane"]),
                        sample_internal_id=row["Sample_ID"],
                        sample_project=row["Sample_Project"],
                        read_number=row["ReadNumber"],
                        sample_bases=row["SampleBases"],
                    )
                )
        return parsed_metrics

    def get_nr_of_header_lines_in_sample_sheet(
        self,
    ) -> int:
        """Return the number of header lines in a sample sheet.
        Any lines before and including the line starting with [Data] is considered the header."""
        with self.sample_sheet_path.open("r") as read_obj:
            csv_reader = csv.reader(read_obj)
            header_line_count: int = 1
            for line in csv_reader:
                if SampleSheetHeaderColumnNames.DATA.value in line:
                    break
                header_line_count += 1
        return header_line_count

    def parse_sample_sheet_file(self):
        """Read in a sample sheet starting from the SAMPLE_SHEET_DATA_HEADER."""
        LOG.info(f"Parsing BCLConvert sample sheet file: {self.sample_sheet_path}")
        header_line_count: int = self.get_nr_of_header_lines_in_sample_sheet()
        sample_sheet: List[BclConvertSampleSheet] = []
        with open(self.sample_sheet_path, "r") as sample_sheet_file:
            for _ in range(header_line_count):
                next(sample_sheet_file)
            reader = csv.DictReader(sample_sheet_file)
            for row in reader:
                sample_sheet.append(
                    BclConvertSampleSheet(
                        flow_cell_name=row["FCID"],
                        lane=row["Lane"],
                        sample_internal_id=row["Sample_ID"],
                        sample_name=row["SampleName"],
                        control=row["Control"],
                        sample_project=row["Sample_Project"],
                    )
                )
        return sample_sheet

    def parse_run_info_file(self) -> BclConvertRunInfo:
        LOG.info(f"Parsing Run info XML {self.run_info_path}")
        parsed_metrics = BclConvertRunInfo(tree=ET.parse(self.run_info_path))
        return parsed_metrics
