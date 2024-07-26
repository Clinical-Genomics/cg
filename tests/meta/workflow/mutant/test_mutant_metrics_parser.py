from pathlib import Path
from cg.meta.workflow.mutant.metrics_parser.metrics_parser import MetricsParser
from cg.meta.workflow.mutant.metrics_parser.models import SampleResults
from cg.store.models import Case


def test_get_raw_results(mutant_results_file_path_qc_pass: Path):
    # GIVEN a path to a valid results file

    # WHEN parsing the file
    MetricsParser.get_raw_results(results_file_path=mutant_results_file_path_qc_pass)

    # THEN no error is thrown


def test_get_validated_results_list(mutant_raw_results_qc_pass):
    # GIVEN a valid raw_results: list[dict[str, Any]] objects

    # WHEN parsing the file
    MetricsParser.get_validated_results_list(raw_results=mutant_raw_results_qc_pass)

    # THEN no error is thrown


def test_get_sample_name_to_id_mapping(mutant_case_qc_pass: Case):
    # GIVEN a case

    # WHEN creating a sample_name_to_id_mapping dict
    sample_name_to_id_mapping: dict[str, str] = MetricsParser.get_sample_name_to_id_mapping(
        case=mutant_case_qc_pass
    )

    # THEN the correct associations are present in the dict
    assert len(sample_name_to_id_mapping) == 2
    assert sample_name_to_id_mapping["23CS503186"] == "sample_qc_pass"
    assert sample_name_to_id_mapping["0PROVSEK"] == "external_negative_control_qc_pass"


def test_get_samples_results(
    mutant_case_qc_pass: Case, mutant_results_list_qc_pass: list[SampleResults]
):
    # GIVEN a case and corresponding results_list

    # WHEN creating a sample_name_to_id_mapping dict
    MetricsParser.get_samples_results(
        case=mutant_case_qc_pass, results_list=mutant_results_list_qc_pass
    )

    # THEN #TODO: Should I create a SampleResults object to assert if it is created correctly?


def test_parse_samples_results(mutant_case_qc_pass: Case, mutant_results_file_path_qc_pass: Path):
    # GIVEN a case and a valid quality metrics file path

    # WHEN parsing the file
    MetricsParser.parse_samples_results(
        case=mutant_case_qc_pass, results_file_path=mutant_results_file_path_qc_pass
    )

    # THEN no error is thrown
