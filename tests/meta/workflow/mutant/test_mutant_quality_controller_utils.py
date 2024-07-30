from pathlib import Path
from cg.meta.workflow.mutant.metrics_parser.models import SampleResults
from cg.meta.workflow.mutant.quality_controller.models import MutantPoolSamples, QualityMetrics
from cg.meta.workflow.mutant.quality_controller.utils import (
    get_internal_negative_control_id_from_lims,
    get_mutant_pool_samples,
    get_quality_metrics,
)
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.mocks.limsmock import MockLimsAPI


def test_test_get_internal_negative_control_id_from_lims(
    mutant_lims: MockLimsAPI, sample_qc_pass: Sample, internal_negative_control_qc_pass: Sample
):
    # GIVEN a sample_id and the internal_id of its corresponding internal_negative_control sample

    sample_internal_id = sample_qc_pass.internal_id
    internal_negative_control_sample_id = internal_negative_control_qc_pass.internal_id

    # WHEN retrieving the internal_negative_control_id_from_lims
    retrieved_internal_negative_control_sample_id = get_internal_negative_control_id_from_lims(
        lims=mutant_lims, sample_internal_id=sample_internal_id
    )

    # THEN no errors are raised and the correct internal_negative_control_id is retrieved
    assert retrieved_internal_negative_control_sample_id == internal_negative_control_sample_id


def test_get_mutant_pool_samples(
    mutant_case_qc_pass: Case,
    mutant_store: Store,
    mutant_lims: MockLimsAPI,
    sample_qc_pass: Sample,
    external_negative_control_qc_pass: Sample,
    internal_negative_control_qc_pass: Sample,
):
    # WHEN creating a MutantPoolSamples object
    mutant_pool_samples: MutantPoolSamples = get_mutant_pool_samples(
        case=mutant_case_qc_pass, status_db=mutant_store, lims=mutant_lims
    )

    # THEN the pool is created correctly:
    #   - the external negative control is identified and separated from the rest of the samples
    #   - all other samples are present in the list under samples
    #   - the internal negative control corresponding to the case is fetched from lims and added to the pool

    assert mutant_pool_samples.external_negative_control == external_negative_control_qc_pass
    assert mutant_pool_samples.samples == [sample_qc_pass]
    assert mutant_pool_samples.internal_negative_control == internal_negative_control_qc_pass


def test_get_quality_metrics(
    mutant_results_file_path_qc_pass: Path,
    mutant_case_qc_pass: Case,
    mutant_store: Store,
    mutant_lims: MockLimsAPI,
    mutant_sample_results_sample_qc_pass: SampleResults,
    sample_qc_pass: Sample,
):
    # GIVEN a case

    # WHEN generating the quality_metrics
    quality_metrics: QualityMetrics = get_quality_metrics(
        case_results_file_path=mutant_results_file_path_qc_pass,
        case=mutant_case_qc_pass,
        status_db=mutant_store,
        lims=mutant_lims,
    )  # QualityMetrics:

    # THEN no errors are raised and the sample_results are created for each sample
    assert (
        quality_metrics.results[sample_qc_pass.internal_id] == mutant_sample_results_sample_qc_pass
    )
