from typing import Any
import pytest

from pathlib import Path

from cg.meta.workflow.mutant.metrics_parser.metrics_parser import MetricsParser
from cg.meta.workflow.mutant.quality_controller.models import (
    CaseQualityResult,
    QualityMetrics,
    SamplesQualityResults,
)

from cg.meta.workflow.mutant.quality_controller.quality_controller import QualityController
from cg.meta.workflow.mutant.quality_controller.report_generator_utils import ReportGenerator
from cg.meta.workflow.mutant.quality_controller.result_logger_utils import ResultLogger
# from cg.meta.workflow.mutant.quality_controller.utils import get_quality_metrics, get_report_path


from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers
from cg.constants.constants import ControlOptions
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
        name="23CS503186",
        control=ControlOptions.EMPTY,
        reads=861966,
        application_tag=application.tag,
    )

    sample_qc_fail = helpers.add_sample(
        store=store,
        internal_id="sample_qc_fail",
        name="23CS102408",
        control=ControlOptions.EMPTY,
        reads=438776,
        application_tag=application.tag,
    )

    external_negative_control_qc_pass = helpers.add_sample(
        store=store,
        internal_id="external_negative_control_qc_pass",
        name="0PROVSEK",
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
        name="23CS503186",
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
        name="0PROVSEK",
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

    # # case_qc_fail_with_failing_controls
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
    sample_qc_pass = LimsSample(id="sample_qc_pass", name="23CS503186")

    sample_qc_fail = LimsSample(id="sample_qc_fail", name="23CS102408")

    external_negative_control_qc_pass = LimsSample(
        id="external_negative_control_qc_pass", name="0PROVSEK", udf=LimsUDF(control="negative")
    )
    internal_negative_control_qc_pass = LimsSample(
        id="internal_negative_control_qc_pass",
        name="internal_negative_control_qc_pass",
        udf=LimsUDF(control="negative", customer="cust000"),
    )

    sample_qc_pass_with_failing_controls = LimsSample(
        id="sample_qc_pass_with_failing_controls", name="23CS503186"
    )

    external_negative_control_qc_fail = LimsSample(
        id="external_negative_control_qc_fail", name="0PROVSEK", udf=LimsUDF(control="negative")
    )

    internal_negative_control_qc_fail = LimsSample(
        id="internal_negative_control_qc_fail",
        name="internal_negative_control_qc_fail",
        udf=LimsUDF(control="negative", customer="cust000"),
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
def mutant_case_qc_pass(mutant_store: Store) -> Case:
    return mutant_store.get_case_by_internal_id("case_qc_pass")


@pytest.fixture
def mutant_analysis_dir_case_qc_pass(mutant_analysis_dir: Path) -> Path:
    return Path(mutant_analysis_dir, "case_qc_pass")


@pytest.fixture
def mutant_results_file_path_qc_pass(mutant_analysis_dir_case_qc_pass: Path) -> Path:
    return Path(mutant_analysis_dir_case_qc_pass, "pass_sars-cov-2_208455_results.csv")


@pytest.fixture
def mutant_raw_results_qc_pass(mutant_results_file_path_qc_pass: Path) -> list[dict[str, Any]]:
    return MetricsParser.get_raw_results(results_file_path=mutant_results_file_path_qc_pass)


@pytest.fixture
def mutant_results_list_qc_pass(mutant_raw_results_qc_pass: list[dict[str, Any]]):
    return MetricsParser.get_validated_results_list(raw_results=mutant_raw_results_qc_pass)


# @pytest.fixture
# def mutant_qc_report_path_case_qc_pass(mutant_analysis_dir_case_qc_pass: Path) -> Path:
#     return get_report_path(case_path=mutant_analysis_dir_case_qc_pass)


@pytest.fixture
def mutant_analysis_dir_case_qc_fail(mutant_analysis_dir: Path) -> Path:
    return Path(mutant_analysis_dir, "case_qc_fail")


@pytest.fixture
def mutant_analysis_dir_case_qc_fail_with_failing_controls(mutant_analysis_dir: Path) -> Path:
    return Path(mutant_analysis_dir, "case_qc_fail_with_failing_controls")


@pytest.fixture
def mutant_results_file_path_qc_fail(mutant_analysis_dir_case_qc_fail: Path) -> Path:
    return Path(mutant_analysis_dir_case_qc_fail, "fail_sars-cov-2_841080_results.csv")


@pytest.fixture
def mutant_results_file_path_qc_fail_with_failing_controls(
    mutant_analysis_dir_case_qc_fail_with_failing_controls: Path,
) -> Path:
    return Path(
        mutant_analysis_dir_case_qc_fail_with_failing_controls,
        "fail_with_failing_controls_sars-cov-2_841080_results.csv",
    )


@pytest.fixture
def sample_qc_pass(mutant_store: Store) -> Sample:
    return mutant_store.get_sample_by_internal_id("sample_qc_pass")


@pytest.fixture
def sample_qc_fail(mutant_store: Store) -> Sample:
    return mutant_store.get_sample_by_internal_id("sample_qc_fail")


@pytest.fixture
def case_qc_pass(mutant_store: Store) -> Case:
    return mutant_store.get_case_by_internal_id("case_qc_pass")


@pytest.fixture
def case_qc_fail(mutant_store: Store) -> Case:
    return mutant_store.get_case_by_internal_id("case_qc_fail")


@pytest.fixture
def case_qc_fail_with_failing_controls(mutant_store: Store) -> Case:
    return mutant_store.get_case_by_internal_id("case_qc_fail_with_failing_controls")


@pytest.fixture
def quality_controller(mutant_store: Store, mutant_lims: MockLimsAPI) -> QualityController:
    return QualityController(
        status_db=mutant_store,
        lims=mutant_lims,
        report_generator=ReportGenerator(),
        result_logger=ResultLogger(),
    )


@pytest.fixture
def quality_metrics_case_qc_pass(
    mutant_results_file_path_qc_pass: Path,
    case_qc_pass: Case,
    mutant_store: Store,
    mutant_lims: MockLimsAPI,
) -> QualityMetrics:
    return get_quality_metrics(
        case_results_file_path=mutant_results_file_path_qc_pass,
        case=case_qc_pass,
        status_db=mutant_store,
        lims=mutant_lims,
    )


@pytest.fixture
def quality_metrics_case_qc_fail(
    mutant_results_file_path_qc_fail: Path,
    case_qc_fail: Case,
    mutant_store: Store,
    mutant_lims: MockLimsAPI,
) -> QualityMetrics:
    return get_quality_metrics(
        case_results_file_path=mutant_results_file_path_qc_fail,
        case=case_qc_fail,
        status_db=mutant_store,
        lims=mutant_lims,
    )


@pytest.fixture
def samples_quality_results_case_qc_pass(
    quality_controller: QualityController, quality_metrics_case_qc_pass: QualityMetrics
) -> SamplesQualityResults:
    return quality_controller.quality_control_samples(quality_metrics=quality_metrics_case_qc_pass)


@pytest.fixture
def case_quality_result_qc_pass(
    quality_controller: QualityController, samples_quality_results: SamplesQualityResults
) -> CaseQualityResult:
    return quality_controller.quality_control_case(samples_quality_results=samples_quality_results)
