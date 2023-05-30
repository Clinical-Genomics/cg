import json

from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import (
    Bcl2FastqTileSequencingMetrics,
)
from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq import (
    parse_bcl2fastq_tile_sequencing_metrics,
)


def test_parse_valid_bcl2fastq_sequencing_metrics(tmp_path, valid_bcl2fastq_metrics_data):
    """Test that valid stats.json files as generated by bcl2fastq in the expected directory structure can be parsed correctly."""
    # GIVEN a valid directory structure with a valid stats.json file
    valid_dir = tmp_path / "l1t1" / "Stats"
    valid_dir.mkdir(parents=True)
    stats_json_path = valid_dir / "stats.json"
    stats_json_path.write_text(json.dumps(valid_bcl2fastq_metrics_data))

    # WHEN parsing the directory containing the valid stats.json file
    result = parse_bcl2fastq_tile_sequencing_metrics(tmp_path)

    # THEN a list of Bcl2FastqTileSequencingMetrics models is returned
    assert isinstance(result, list)
    assert all(isinstance(item, Bcl2FastqTileSequencingMetrics) for item in result)

    # THEN the Bcl2FastqTileSequencingMetrics model contains the expected data
    assert result[0].flow_cell_name == valid_bcl2fastq_metrics_data["Flowcell"]
    assert result[0].run_number == valid_bcl2fastq_metrics_data["RunNumber"]
    assert result[0].run_id == valid_bcl2fastq_metrics_data["RunId"]
