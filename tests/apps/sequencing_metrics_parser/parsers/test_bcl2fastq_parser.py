import json

from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import Bcl2FastqSequencingMetrics
from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq import parse_bcl2fastq_sequencing_metrics


def test_parse_bcl2fastq_sequencing_metrics(tmp_path, valid_bcl2fastq_metrics_data):
    # GIVEN a valid stats.json file
    stats_json_path = tmp_path / "stats.json"
    stats_json_path.write_text(json.dumps(valid_bcl2fastq_metrics_data))

    # WHEN parsing the valid stats.json file
    result = parse_bcl2fastq_sequencing_metrics(str(stats_json_path))

    # THEN a Bcl2FastqSequencingMetrics model is returned
    assert isinstance(result, Bcl2FastqSequencingMetrics)

    # THEN the Bcl2FastqSequencingMetrics model contains the expected data
    assert result.flowcell == valid_bcl2fastq_metrics_data["Flowcell"]
    assert result.run_number == valid_bcl2fastq_metrics_data["RunNumber"]
    assert result.run_id == valid_bcl2fastq_metrics_data["RunId"]
