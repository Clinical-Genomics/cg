import logging
from typing import List

from cg.apps.cgstats.parsers.conversion_stats import (
    ConversionStats,
    SampleConversionResults,
    UnknownBarcode,
)
from pydantic import BaseModel
from typing_extensions import Literal

LOG = logging.getLogger(__name__)
MIN_CLUSTER_COUNT = 1000000
DEMUX_REPORT_HEADER: List[str] = ["BARCODE", "SAMPLE", "TYPE", "LANE", "READ_COUNT"]


class SampleData(BaseModel):
    read_count: int
    barcode: str
    lane: int
    sample: str = "Unknown"
    type: Literal["sample", "unknown-barcode"]


def get_low_count_samples(samples: List[SampleConversionResults], lane: int) -> List[SampleData]:
    """return all samples with cluster count below a certain threshold"""
    low_samples: List[SampleData] = []
    for sample in samples:
        if sample.pass_filter_cluster_count >= MIN_CLUSTER_COUNT:
            continue
        low_samples.append(
            SampleData(
                read_count=sample.pass_filter_cluster_count,
                barcode=sample.barcode,
                lane=lane,
                sample=sample.sample_id,
                type="sample",
            )
        )
    return low_samples


def get_unknown_barcodes(unknown_barcodes: List[UnknownBarcode], lane: int) -> List[SampleData]:
    LOG.info("Adding unknown barcodes for lane %s", lane)
    return [
        SampleData(
            read_count=unknown.read_count,
            barcode=unknown.barcode,
            lane=lane,
            type="unknown-barcode",
        )
        for unknown in unknown_barcodes
    ]


def get_demux_report_data(
    conversion_stats: ConversionStats, skip_empty: bool = False
) -> List[SampleData]:
    """create a list of rows with report data from a ConversionStats object

    If skip_empty the report will be empty if there are no samples with low cluster counts
    """
    report_data: List[SampleData] = []
    for lane, barcode_to_result in conversion_stats.lanes_to_barcode.items():
        lane_samples = get_low_count_samples(
            samples=[barcode_to_result[barcode] for barcode in barcode_to_result], lane=lane
        )
        if lane_samples:
            report_data.extend(lane_samples)
    if skip_empty and not report_data:
        return report_data
    for lane, barcode_data in conversion_stats.lanes_to_unknown_barcode.items():
        report_data.extend(get_unknown_barcodes(unknown_barcodes=barcode_data, lane=lane))
    return report_data


def create_demux_report(conversion_stats: ConversionStats, skip_empty: bool = False) -> List[str]:
    """Find the barcodes from each lane with low number of reads and create a report"""
    report_content: List[str] = ["\t".join(DEMUX_REPORT_HEADER)]
    report_data = get_demux_report_data(conversion_stats=conversion_stats, skip_empty=skip_empty)
    for sample_data in report_data:
        report_content.append(
            "\t".join(
                [
                    sample_data.barcode,
                    sample_data.sample,
                    sample_data.type,
                    str(sample_data.lane),
                    str(sample_data.read_count),
                ]
            )
        )
    return report_content
