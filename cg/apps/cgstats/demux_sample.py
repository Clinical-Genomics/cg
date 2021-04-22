"""Get samples with information from demultiplexing"""
from pathlib import Path
from typing import Dict

from cg.apps.cgstats.parsers.conversion_stats import ConversionStats, SampleConversionResults
from cg.apps.cgstats.parsers.demux_stats import DemuxStats, SampleBarcodeStats
from cgmodels.demultiplex.sample_sheet import NovaSeqSample, SampleSheet
from pydantic import BaseModel


class DemuxSample(BaseModel):
    """Gather statistics from the demultiplexing results for a sample"""

    sample_name: str
    flowcell: str
    lane: int
    raw_clusters_pc: float
    pass_filter_clusters: int
    pass_filter_yield_pc: float
    pass_filter_yield: int
    pass_filter_Q30: float
    pass_filter_read1_q30: float
    pass_filter_read2_q30: float
    pass_filter_qscore: float
    undetermined_pc: float
    barcodes: int
    perfect_barcodes: int
    one_mismatch_barcodes: int = 0


def create_demux_sample(
    sample_id: str,
    flowcell: str,
    lane: int,
    barcode_stats: SampleBarcodeStats,
    conversion_stats: SampleConversionResults,
    nr_raw_clusters: int,
) -> DemuxSample:
    return DemuxSample(
        sample_name=sample_id,
        flowcell=flowcell,
        lane=lane,
        raw_clusters_pc=round(conversion_stats.raw_cluster_count / nr_raw_clusters * 100, 2),
        pass_filter_clusters=conversion_stats.pass_filter_cluster_count,
        pass_filter_yield_pc=round(
            conversion_stats.pass_filter_yield / conversion_stats.raw_yield * 100,
            2,
        )
        if conversion_stats.raw_yield
        else 0,
        pass_filter_yield=conversion_stats.pass_filter_yield,
        pass_filter_Q30=round(
            conversion_stats.pass_filter_q30 / conversion_stats.pass_filter_yield * 100,
            2,
        )
        if conversion_stats.pass_filter_yield
        else 0,
        pass_filter_read1_q30=round(
            conversion_stats.pass_filter_read1_q30 / conversion_stats.pass_filter_read1_yield * 100,
            2,
        )
        if conversion_stats.pass_filter_read1_yield
        else 0,
        pass_filter_read2_q30=round(
            conversion_stats.pass_filter_read2_q30 / conversion_stats.pass_filter_read2_yield * 100,
            2,
        )
        if conversion_stats.pass_filter_read2_yield
        else 0,
        pass_filter_qscore=round(
            conversion_stats.pass_filter_quality_score_sum / conversion_stats.pass_filter_yield,
            2,
        )
        if conversion_stats.pass_filter_yield
        else 0,
        undetermined_pc=(conversion_stats.pass_filter_cluster_count - barcode_stats.barcode_count)
        / conversion_stats.pass_filter_cluster_count
        * 100
        if conversion_stats.pass_filter_cluster_count
        else 0,
        barcodes=barcode_stats.barcode_count,
        perfect_barcodes=barcode_stats.perfect_barcode_count,
        one_mismatch_barcodes=barcode_stats.one_mismatch_barcode_count,
    )


def get_demux_samples(
    conversion_stats_path: Path, demux_stats_path: Path, sample_sheet: SampleSheet
) -> Dict[int, Dict[str, DemuxSample]]:
    """Gather information from demultiplexing results and create samples with the correct information"""
    demux_samples: Dict[int, Dict[str, DemuxSample]] = {}
    demux_stats_parser: DemuxStats = DemuxStats(stats_file=demux_stats_path)
    conversion_stats_parser: ConversionStats = ConversionStats(
        conversion_stats=conversion_stats_path
    )
    raw_clusters: Dict[int, int] = conversion_stats_parser.raw_clusters_per_lane
    flowcell_id: str = conversion_stats_parser.flowcell_id
    sample: NovaSeqSample
    for sample in sample_sheet.samples:
        lane: int = sample.lane
        if lane not in demux_samples:
            demux_samples[lane] = {}
        barcode = (
            "+".join([sample.index, sample.second_index]) if sample.second_index else sample.index
        )
        barcode_stats: SampleBarcodeStats = demux_stats_parser.lanes_to_barcode[lane][barcode]
        conversion_stats: SampleConversionResults = conversion_stats_parser.lanes_to_barcode[lane][
            barcode
        ]
        lane_raw_cluster: int = raw_clusters[lane]
        sample_id: str = sample.sample_id
        demux_samples[lane][sample_id] = create_demux_sample(
            sample_id=sample_id,
            flowcell=flowcell_id,
            lane=lane,
            barcode_stats=barcode_stats,
            conversion_stats=conversion_stats,
            nr_raw_clusters=lane_raw_cluster,
        )

    return demux_samples


if __name__ == "__main__":
    from cgmodels.demultiplex.sample_sheet import get_sample_sheet_from_file

    small_run = False
    small_set = {
        "conversion": Path(
            "/Users/mans.magnusson/PycharmProjects/cg/local/SmallConversionStats.xml"
        ),
        "demux": Path(
            "/Users/mans.magnusson/PycharmProjects/cg/local/SmallDemultiplexingStats.xml"
        ),
        "sample_sheet": Path("/Users/mans.magnusson/PycharmProjects/cg/local/SmallSampleSheet.csv"),
    }
    full_set = {
        "conversion": Path("/Users/mans.magnusson/PycharmProjects/cg/local/ConversionStats.xml"),
        "demux": Path("/Users/mans.magnusson/PycharmProjects/cg/local/DemultiplexingStats.xml"),
        "sample_sheet": Path("/Users/mans.magnusson/PycharmProjects/cg/local/SampleSheet.csv"),
    }
    files = small_set
    if not small_run:
        files = full_set
    result = get_demux_samples(
        conversion_stats_path=files["conversion"],
        demux_stats_path=files["demux"],
        sample_sheet=get_sample_sheet_from_file(files["sample_sheet"], sheet_type="S4"),
    )
    for lane_nr in result.keys():
        print(f"Nr samples in lane {lane_nr}: {len(result[lane_nr])}")
