from pathlib import Path
from cg.meta.workflow.mutant.quality_controller.models import (
    MutantPoolSamples,
    QualityMetrics,
    SampleResults,
)
from cg.meta.workflow.mutant.quality_controller.quality_controller import MutantQualityController
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


def test_get_quality_metrics(
    mutant_quality_controller: MutantQualityController,
    mutant_results_file_path_case_qc_pass: Path,
    mutant_case_qc_pass: Case,
    mutant_sample_results_sample_qc_pass: SampleResults,
    sample_qc_pass: Sample,
):
    # GIVEN a case

    # WHEN generating the quality_metrics
    quality_metrics: QualityMetrics = mutant_quality_controller._get_quality_metrics(
        case_results_file_path=mutant_results_file_path_case_qc_pass,
        case=mutant_case_qc_pass,
    )

    # THEN no errors are raised and the sample_results are created for each sample
    assert (
        quality_metrics.results[sample_qc_pass.internal_id] == mutant_sample_results_sample_qc_pass
    )
