from pathlib import Path
from cg.meta.workflow.mutant.metrics_parser.metrics_parser import MetricsParser


def test_parse_valid_quality_metrics(mutant_results_file_path_qc_pass: Path):
    # GIVEN a valid quality metrics file path

    # WHEN parsing the file
    MetricsParser.parse_samples_results(mutant_results_file_path_qc_pass)

    # THEN no error is thrown
