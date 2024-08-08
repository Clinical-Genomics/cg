from pathlib import Path
from cg.meta.workflow.mutant.quality_controller.metrics_parser_utils import MetricsParser
from cg.meta.workflow.mutant.metrics_parser.models import SampleResults
from cg.store.models import Case, Sample


def test__get_validated_results_list(mutant_results_file_path_qc_pass: Path):
    # GIVEN a valid raw_results: list[dict[str, Any]] objects

    # WHEN parsing the file
    MetricsParser._get_validated_results_list(results_file_path=mutant_results_file_path_qc_pass)

    # THEN no error is thrown


def test__get_sample_name_to_id_mapping(mutant_case_qc_pass: Case):
    # GIVEN a case

    # WHEN creating a sample_name_to_id_mapping dict
    sample_name_to_id_mapping: dict[str, str] = MetricsParser._get_sample_name_to_id_mapping(
        case=mutant_case_qc_pass
    )

    # THEN the correct associations are present in the dict
    assert len(sample_name_to_id_mapping) == 2
    assert sample_name_to_id_mapping["sample_qc_pass"] == "sample_qc_pass"
    assert (
        sample_name_to_id_mapping["external_negative_control_qc_pass"]
        == "external_negative_control_qc_pass"
    )


def test__get_samples_results(
    mutant_case_qc_pass: Case,
    mutant_results_list_qc_pass: list[SampleResults],
    sample_qc_pass: Sample,
):
    # GIVEN a case and corresponding results_list

    # WHEN creating a sample_name_to_id_mapping dict
    samples_results: dict[str, SampleResults] = MetricsParser._get_samples_results(
        case=mutant_case_qc_pass, results_list=mutant_results_list_qc_pass
    )

    # THEN the samples_results object has the correct structure
    assert isinstance(samples_results, dict)
    assert isinstance(samples_results[sample_qc_pass.internal_id], SampleResults)


def test_parse_samples_results(mutant_case_qc_pass: Case, mutant_results_file_path_qc_pass: Path):
    # GIVEN a case and a valid quality metrics file path

    # WHEN parsing the file
    samples_results: dict[str, SampleResults] = MetricsParser.parse_samples_results(
        case=mutant_case_qc_pass, results_file_path=mutant_results_file_path_qc_pass
    )

    # THEN no error is thrown and sample_qc_pass passes QC
    assert samples_results["sample_qc_pass"].qc_pass is True
