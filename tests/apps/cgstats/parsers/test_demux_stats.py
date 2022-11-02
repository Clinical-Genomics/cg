from pathlib import Path

from cg.apps.cgstats.parsers.demux_stats import DemuxStats


def test_parse_demux_stats(demultiplexing_stats_path: Path):
    # GIVEN an existing demultiplexing stats file
    assert demultiplexing_stats_path.exists()
    # GIVEN that the file have some content
    demux_info: str = demultiplexing_stats_path.read_text()
    assert demux_info

    # WHEN instantiating a demux stats parser
    parser: DemuxStats = DemuxStats(demux_stats_path=demultiplexing_stats_path)

    # THEN assert that the parser have some content
    assert parser.lanes_to_barcode
