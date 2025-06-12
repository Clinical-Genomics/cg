from pathlib import Path
from cg.meta.workflow.mutant.quality_controller.models import (
    MutantPoolSamples,
    MutantQualityResult,
    CaseQualityResult,
    SampleQualityResults,
    SamplesQualityResults,
    ParsedSampleResults,
    SamplePoolAndResults,
)
from cg.meta.workflow.mutant.quality_controller.quality_controller import (
    MutantQualityController,
)
from cg.store.models import Case, Sample


def test_get_mutant_pool_samples(
    mutant_quality_controller: MutantQualityController,
    mutant_case_qc_pass: Case,
    sample_qc_pass: Sample,
    external_negative_control_qc_pass: Sample,
    internal_negative_control_qc_pass: Sample,
):
    # WHEN creating a MutantPoolSamples object
    mutant_pool_samples: MutantPoolSamples = mutant_quality_controller._get_mutant_pool_samples(
        case=mutant_case_qc_pass
    )

    # THEN the pool is created correctly:
    #   - the external negative control is identified and separated from the rest of the samples
    #   - all other samples are present in the list under samples
    #   - the internal negative control corresponding to the case is fetched from lims and added to the pool

    assert mutant_pool_samples.external_negative_control == external_negative_control_qc_pass
    assert mutant_pool_samples.samples == [sample_qc_pass]
    assert mutant_pool_samples.internal_negative_control == internal_negative_control_qc_pass


def test_get_sample_pool_and_results(
    mutant_quality_controller: MutantQualityController,
    mutant_results_file_path_case_qc_pass: Path,
    mutant_case_qc_pass: Case,
    mutant_sample_results_sample_qc_pass: ParsedSampleResults,
    sample_qc_pass: Sample,
):
    # GIVEN a case

    # WHEN generating the quality_metrics
    sample_pool_and_results: SamplePoolAndResults = (
        mutant_quality_controller._get_sample_pool_and_results(
            case_results_file_path=mutant_results_file_path_case_qc_pass,
            case=mutant_case_qc_pass,
        )
    )

    # THEN no errors are raised and the sample_results are created for each sample
    assert (
        sample_pool_and_results.results[sample_qc_pass.internal_id]
        == mutant_sample_results_sample_qc_pass
    )


def test_get_sample_quality_result_for_sample(
    mutant_quality_controller: MutantQualityController,
    sample_qc_pass: Sample,
    mutant_sample_results_sample_qc_pass: ParsedSampleResults,
):
    # GIVEN a sample that passes qc and its corresponding SampleResults

    # WHEN peforming quality control on the sample
    sample_quality_results_sample_qc_pass: SampleQualityResults = (
        mutant_quality_controller._get_sample_quality_result_for_sample(
            sample=sample_qc_pass,
            sample_results=mutant_sample_results_sample_qc_pass,
        )
    )
    # THEN the sample passes qc
    assert sample_quality_results_sample_qc_pass.passes_qc is True


def test_get_sample_quality_result_for_internal_negative_control_sample(
    mutant_quality_controller: MutantQualityController,
    internal_negative_control_qc_pass: Sample,
):
    # GIVEN an internal negative control sample that passes qc and its corresponding SampleResults

    # WHEN peforming quality control on the sample
    sample_quality_results_sample_qc_pass: SampleQualityResults = (
        mutant_quality_controller._get_sample_quality_result_for_internal_negative_control_sample(
            sample=internal_negative_control_qc_pass,
        )
    )
    # THEN the sample passes qc
    assert sample_quality_results_sample_qc_pass.passes_qc is True


def test_get_sample_quality_result_for_external_negative_control_sample(
    mutant_quality_controller: MutantQualityController,
    external_negative_control_qc_pass: Sample,
    mutant_sample_results_external_negative_control_qc_pass: ParsedSampleResults,
):
    # GIVEN an external negative control sample that passes qc and its corresponding SampleResults

    # WHEN peforming quality control on the sample
    sample_quality_results_sample_qc_pass: SampleQualityResults = (
        mutant_quality_controller._get_sample_quality_result_for_external_negative_control_sample(
            sample=external_negative_control_qc_pass,
            sample_results=mutant_sample_results_external_negative_control_qc_pass,
        )
    )
    # THEN the sample passes qc
    assert sample_quality_results_sample_qc_pass.passes_qc is True


def test_get_samples_quality_results(
    mutant_quality_controller: MutantQualityController,
    mutant_sample_pool_and_results_case_qc_pass: SamplePoolAndResults,
):
    # GIVEN a quality metrics objrect from a case where all samples pass QC

    # WHEN performing quality control on all the samples
    samples_quality_results: SamplesQualityResults = (
        mutant_quality_controller._get_samples_quality_results(
            sample_pool_and_results=mutant_sample_pool_and_results_case_qc_pass
        )
    )

    # THEN no error is raised and the correct quality results are generated
    assert samples_quality_results.internal_negative_control.passes_qc is True
    assert samples_quality_results.external_negative_control.passes_qc is True
    assert len(samples_quality_results.samples) == 1
    samples_pass_qc = [
        sample_quality_results.passes_qc
        for sample_quality_results in samples_quality_results.samples
    ]
    assert all(samples_pass_qc) is True


def test_get_case_quality_result(
    mutant_quality_controller: MutantQualityController,
    samples_quality_results_case_qc_pass: SamplesQualityResults,
):
    # GIVEN a samples_quality_results object for a case that passes QC

    # WHEN performing QC on the case
    case_quality_result: CaseQualityResult = mutant_quality_controller._get_case_quality_result(
        samples_quality_results=samples_quality_results_case_qc_pass
    )

    # THEN the correct result is generated
    assert case_quality_result.passes_qc is True
    assert case_quality_result.internal_negative_control_passes_qc is True
    assert case_quality_result.external_negative_control_passes_qc is True


def test_get_quality_control_result_case_qc_pass(
    mutant_quality_controller: MutantQualityController,
    mutant_case_qc_pass: Case,
    mutant_results_file_path_case_qc_pass: Path,
    mutant_qc_report_path_case_qc_pass: Path,
):
    # GIVEN a case that passes QC

    # WHEN performing QC on the case

    case_quality_result: MutantQualityResult = mutant_quality_controller.get_quality_control_result(
        case=mutant_case_qc_pass,
        case_results_file_path=mutant_results_file_path_case_qc_pass,
        case_qc_report_path=mutant_qc_report_path_case_qc_pass,
    )

    # THEN the case passes qc
    assert case_quality_result.passes_qc is True
    assert case_quality_result.case_quality_result.external_negative_control_passes_qc is True
    assert case_quality_result.case_quality_result.internal_negative_control_passes_qc is True


def test_get_quality_control_result_case_qc_fail(
    mutant_quality_controller: MutantQualityController,
    mutant_case_qc_fail: Case,
    mutant_results_file_path_qc_fail: Path,
    mutant_qc_report_path_case_qc_fail: Path,
):
    # GIVEN a case that passes QC

    # WHEN performing QC on the case

    case_quality_result: MutantQualityResult = mutant_quality_controller.get_quality_control_result(
        case=mutant_case_qc_fail,
        case_results_file_path=mutant_results_file_path_qc_fail,
        case_qc_report_path=mutant_qc_report_path_case_qc_fail,
    )

    # THEN the case passes qc
    assert case_quality_result.passes_qc is False
    assert case_quality_result.case_quality_result.external_negative_control_passes_qc is True
    assert case_quality_result.case_quality_result.internal_negative_control_passes_qc is True


def test_get_quality_control_result_case_qc_fail_with_failing_controls(
    mutant_quality_controller: MutantQualityController,
    mutant_case_qc_fail_with_failing_controls: Case,
    mutant_results_file_path_qc_fail_with_failing_controls: Path,
    mutant_qc_report_path_case_qc_fail_with_failing_controls: Path,
):
    # GIVEN a case that does not passe QC due to failing control samples

    # WHEN performing QC on the case

    case_quality_result: MutantQualityResult = mutant_quality_controller.get_quality_control_result(
        case=mutant_case_qc_fail_with_failing_controls,
        case_results_file_path=mutant_results_file_path_qc_fail_with_failing_controls,
        case_qc_report_path=mutant_qc_report_path_case_qc_fail_with_failing_controls,
    )

    # THEN the case does not pass QC and the correct result is retrieved for the control samples
    assert case_quality_result.passes_qc is False
    assert case_quality_result.case_quality_result.external_negative_control_passes_qc is False
    assert case_quality_result.case_quality_result.internal_negative_control_passes_qc is False
