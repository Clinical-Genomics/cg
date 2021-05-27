from pathlib import Path

from cg.apps.cgstats.parsers.conversion_stats import ConversionStats


def test_parse_demux_stats(conversion_stats_path: Path):
    # GIVEN an existing conversion stats file
    assert conversion_stats_path.exists()
    # GIVEN that the file have some content
    demux_info: str = conversion_stats_path.read_text()
    assert demux_info

    # WHEN instantiating a conversion stats parser
    parser: ConversionStats = ConversionStats(conversion_stats_path=conversion_stats_path)

    # THEN assert that the the parser have some content
    assert parser.lanes_to_barcode
