from pathlib import Path
from cg.meta.workflow.mutant.metrics_parser.metrics_parser import MetricsParser
from cg.store.models import Case
from cg.store.store import Store


def test_parse_valid_quality_metrics(mutant_store: Store, mutant_results_file_path_qc_pass: Path):
    # GIVEN a case and a valid quality metrics file path
    case: Case = mutant_store.get_case_by_internal_id("case_qc_pass")

    # WHEN parsing the file
    MetricsParser.parse_samples_results(case=case, file_path=mutant_results_file_path_qc_pass)

    # THEN no error is thrown
