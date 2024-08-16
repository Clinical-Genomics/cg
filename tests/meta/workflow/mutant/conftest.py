import pytest

from pathlib import Path

from cg.meta.workflow.mutant.quality_controller.metrics_parser_utils import (
    _get_validated_results_list,
    parse_samples_results,
)
from cg.meta.workflow.mutant.quality_controller.models import (
    SamplePoolAndResults,
    ParsedSampleResults,
    SamplesQualityResults,
)
from cg.meta.workflow.mutant.quality_controller.quality_controller import MutantQualityController
from cg.store.models import Case, Sample
from cg.store.store import Store
from cg.constants.constants import ControlOptions, MutantQC
from tests.store_helpers import StoreHelpers
from tests.mocks.limsmock import LimsSample, LimsUDF, MockLimsAPI


@pytest.fixture
def mutant_store(store: Store, helpers: StoreHelpers) -> Store:
    # Add mutant application and application_version
    application = helpers.add_application(
        store=store, application_tag="VWGDPTR001", target_reads=2000000, percent_reads_guaranteed=1
    )

    # Add cases
    case_qc_pass = helpers.add_case(store=store, name="case_qc_pass", internal_id="case_qc_pass")
    case_qc_fail = helpers.add_case(store=store, name="case_qc_fail", internal_id="case_qc_fail")

    case_qc_fail_with_failing_controls = helpers.add_case(
        store=store,
        name="case_qc_fail_with_failing_controls",
        internal_id="case_qc_fail_with_failing_controls",
    )

    # Add samples
    sample_qc_pass = helpers.add_sample(
        store=store,
        internal_id="sample_qc_pass",
        name="sample_qc_pass",
        control=ControlOptions.EMPTY,
        reads=861966,
        application_tag=application.tag,
    )

    sample_qc_fail = helpers.add_sample(
        store=store,
        internal_id="sample_qc_fail",
        name="sample_qc_fail",
        control=ControlOptions.EMPTY,
        reads=438776,
        application_tag=application.tag,
    )

    external_negative_control_qc_pass = helpers.add_sample(
        store=store,
        internal_id="external_negative_control_qc_pass",
        name="external_negative_control_qc_pass",
        control=ControlOptions.NEGATIVE,
        reads=20674,
        application_tag=application.tag,
    )

    internal_negative_control_qc_pass = helpers.add_sample(
        store=store,
        internal_id="internal_negative_control_qc_pass",
        name="internal_negative_control_qc_pass",
        control=ControlOptions.NEGATIVE,
        reads=0,
        application_tag=application.tag,
    )

    sample_qc_pass_with_failing_controls = helpers.add_sample(
        store=store,
        internal_id="sample_qc_pass_with_failing_controls",
        name="sample_qc_pass",
        control=ControlOptions.EMPTY,
        reads=861966,
        application_tag=application.tag,
    )

    internal_negative_control_qc_fail = helpers.add_sample(
        store=store,
        internal_id="internal_negative_control_qc_fail",
        name="internal_negative_control_qc_fail",
        control=ControlOptions.NEGATIVE,
        reads=3000,
        application_tag=application.tag,
    )

    external_negative_control_qc_fail = helpers.add_sample(
        store=store,
        internal_id="external_negative_control_qc_fail",
        name="external_negative_control_qc_fail",
        control=ControlOptions.NEGATIVE,
        reads=200000,
        application_tag=application.tag,
    )

    # Add CaseSample relationships
    # case_qc_pass
    helpers.add_relationship(store=store, case=case_qc_pass, sample=sample_qc_pass)
    helpers.add_relationship(
        store=store, case=case_qc_pass, sample=external_negative_control_qc_pass
    )

    # case_qc_fail
    helpers.add_relationship(store=store, case=case_qc_fail, sample=sample_qc_fail)
    helpers.add_relationship(
        store=store, case=case_qc_fail, sample=external_negative_control_qc_pass
    )

    # case_qc_fail_with_failing_controls
    helpers.add_relationship(
        store=store,
        case=case_qc_fail_with_failing_controls,
        sample=sample_qc_pass_with_failing_controls,
    )
    helpers.add_relationship(
        store=store,
        case=case_qc_fail_with_failing_controls,
        sample=external_negative_control_qc_fail,
    )

    return store


@pytest.fixture
def mutant_lims(lims_api: MockLimsAPI) -> MockLimsAPI:
    # Get samples
    sample_qc_pass = LimsSample(id="sample_qc_pass", name="sample_qc_pass")

    sample_qc_fail = LimsSample(id="sample_qc_fail", name="sample_qc_fail")

    external_negative_control_qc_pass = LimsSample(
        id="external_negative_control_qc_pass",
        name="external_negative_control_qc_pass",
        udfs=LimsUDF(control="negative"),
    )
    internal_negative_control_qc_pass = LimsSample(
        id="internal_negative_control_qc_pass",
        name="internal_negative_control_qc_pass",
        udfs=LimsUDF(control="negative", customer="cust000"),
    )

    sample_qc_pass_with_failing_controls = LimsSample(
        id="sample_qc_pass_with_failing_controls", name="sample_qc_pass"
    )

    external_negative_control_qc_fail = LimsSample(
        id="external_negative_control_qc_fail",
        name="external_negative_control_qc_fail",
        udfs=LimsUDF(control="negative"),
    )

    internal_negative_control_qc_fail = LimsSample(
        id="internal_negative_control_qc_fail",
        name="internal_negative_control_qc_fail",
        udfs=LimsUDF(control="negative", customer="cust000"),
    )

    # Create pools
    samples_qc_pass = [
        sample_qc_pass,
        external_negative_control_qc_pass,
        internal_negative_control_qc_pass,
    ]

    samples_qc_fail = [
        sample_qc_fail,
        external_negative_control_qc_pass,
        internal_negative_control_qc_pass,
    ]

    samples_qc_fail_with_failing_controls = [
        sample_qc_pass_with_failing_controls,
        external_negative_control_qc_fail,
        internal_negative_control_qc_fail,
    ]

    # Add pool artifacts
    lims_api.add_artifact_for_sample(sample_id=sample_qc_pass.id, samples=samples_qc_pass)
    lims_api.add_artifact_for_sample(sample_id=sample_qc_fail.id, samples=samples_qc_fail)

    lims_api.add_artifact_for_sample(
        sample_id=sample_qc_pass_with_failing_controls.id,
        samples=samples_qc_fail_with_failing_controls,
    )

    return lims_api


@pytest.fixture
def mutant_quality_controller(
    mutant_store: Store, mutant_lims: MockLimsAPI
) -> MutantQualityController:
    return MutantQualityController(status_db=mutant_store, lims=mutant_lims)


# Samples
@pytest.fixture
def sample_qc_pass(mutant_store: Store) -> Sample:
    return mutant_store.get_sample_by_internal_id("sample_qc_pass")


@pytest.fixture
def internal_negative_control_qc_pass(mutant_store: Store) -> Sample:
    return mutant_store.get_sample_by_internal_id("internal_negative_control_qc_pass")


@pytest.fixture
def external_negative_control_qc_pass(mutant_store: Store) -> Sample:
    return mutant_store.get_sample_by_internal_id("external_negative_control_qc_pass")


@pytest.fixture
def sample_qc_fail(mutant_store: Store) -> Sample:
    return mutant_store.get_sample_by_internal_id("sample_qc_fail")


# Cases
## mutant_case_qc_pass
@pytest.fixture
def mutant_case_qc_pass(mutant_store: Store) -> Case:
    return mutant_store.get_case_by_internal_id("case_qc_pass")


@pytest.fixture
def mutant_analysis_dir_case_qc_pass(mutant_analysis_dir: Path, mutant_case_qc_pass: Case) -> Path:
    return Path(mutant_analysis_dir, mutant_case_qc_pass.internal_id)


@pytest.fixture
def mutant_results_file_path_case_qc_pass(mutant_analysis_dir_case_qc_pass: Path) -> Path:
    return Path(mutant_analysis_dir_case_qc_pass, "pass_sars-cov-2_208455_results.csv")


@pytest.fixture
def mutant_qc_report_path_case_qc_pass(mutant_analysis_dir_case_qc_pass: Path) -> Path:
    return mutant_analysis_dir_case_qc_pass.joinpath(MutantQC.QUALITY_REPORT_FILE_NAME)


@pytest.fixture
def mutant_results_list_qc_pass(mutant_results_file_path_case_qc_pass: Path):
    return _get_validated_results_list(results_file_path=mutant_results_file_path_case_qc_pass)


@pytest.fixture
def mutant_sample_pool_and_results_case_qc_pass(
    mutant_quality_controller: MutantQualityController,
    mutant_results_file_path_case_qc_pass: Path,
    mutant_case_qc_pass: Case,
) -> SamplePoolAndResults:
    return mutant_quality_controller._get_sample_pool_and_results(
        case_results_file_path=mutant_results_file_path_case_qc_pass,
        case=mutant_case_qc_pass,
    )


@pytest.fixture
def mutant_samples_results_case_qc_pass(
    mutant_case_qc_pass: Case, mutant_results_file_path_case_qc_pass: Path
) -> dict[str, ParsedSampleResults]:
    return parse_samples_results(
        case=mutant_case_qc_pass, results_file_path=mutant_results_file_path_case_qc_pass
    )


@pytest.fixture
def mutant_sample_results_sample_qc_pass(
    sample_qc_pass: Sample, mutant_samples_results_case_qc_pass: dict[str, ParsedSampleResults]
) -> ParsedSampleResults:
    sample_results = mutant_samples_results_case_qc_pass[sample_qc_pass.internal_id]
    return sample_results


@pytest.fixture
def mutant_sample_results_external_negative_control_qc_pass(
    external_negative_control_qc_pass: Sample,
    mutant_samples_results_case_qc_pass: dict[str, ParsedSampleResults],
) -> ParsedSampleResults:
    sample_results = mutant_samples_results_case_qc_pass[
        external_negative_control_qc_pass.internal_id
    ]
    return sample_results


@pytest.fixture
def samples_quality_results_case_qc_pass(
    mutant_quality_controller: MutantQualityController,
    mutant_sample_pool_and_results_case_qc_pass: SamplePoolAndResults,
) -> SamplesQualityResults:
    return mutant_quality_controller._get_samples_quality_results(
        sample_pool_and_results=mutant_sample_pool_and_results_case_qc_pass
    )


## mutant_case_qc_fail
@pytest.fixture
def mutant_case_qc_fail(mutant_store: Store) -> Case:
    return mutant_store.get_case_by_internal_id("case_qc_fail")


@pytest.fixture
def mutant_analysis_dir_case_qc_fail(mutant_analysis_dir: Path, mutant_case_qc_fail: Case) -> Path:
    return Path(mutant_analysis_dir, mutant_case_qc_fail.internal_id)


@pytest.fixture
def mutant_results_file_path_qc_fail(mutant_analysis_dir_case_qc_fail: Path) -> Path:
    return Path(mutant_analysis_dir_case_qc_fail, "fail_sars-cov-2_841080_results.csv")


@pytest.fixture
def mutant_qc_report_path_case_qc_fail(mutant_analysis_dir_case_qc_fail: Path) -> Path:
    return mutant_analysis_dir_case_qc_fail.joinpath(MutantQC.QUALITY_REPORT_FILE_NAME)


## mutant_case_qc_fail_with_failing_controls
@pytest.fixture
def mutant_case_qc_fail_with_failing_controls(mutant_store: Store) -> Case:
    return mutant_store.get_case_by_internal_id("case_qc_fail_with_failing_controls")


@pytest.fixture
def mutant_analysis_dir_case_qc_fail_with_failing_controls(
    mutant_analysis_dir: Path, mutant_case_qc_fail_with_failing_controls: Case
) -> Path:
    return Path(mutant_analysis_dir, mutant_case_qc_fail_with_failing_controls.internal_id)


@pytest.fixture
def mutant_results_file_path_qc_fail_with_failing_controls(
    mutant_analysis_dir_case_qc_fail_with_failing_controls: Path,
) -> Path:
    return Path(
        mutant_analysis_dir_case_qc_fail_with_failing_controls,
        "fail_with_failing_controls_sars-cov-2_841080_results.csv",
    )


@pytest.fixture
def mutant_qc_report_path_case_qc_fail_with_failing_controls(
    mutant_analysis_dir_case_qc_fail_with_failing_controls: Path,
) -> Path:
    return mutant_analysis_dir_case_qc_fail_with_failing_controls.joinpath(
        MutantQC.QUALITY_REPORT_FILE_NAME
    )
