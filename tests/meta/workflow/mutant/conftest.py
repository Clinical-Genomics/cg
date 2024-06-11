import pytest

from pathlib import Path

from cg.constants import Workflow, DataDelivery
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Sample, CaseSample, Application, ApplicationVersion
from cg.store.store import Store
from tests.store_helpers import StoreHelpers
from cg.constants.constants import ControlOptions


@pytest.fixture(name="failing_report_path")
def failing_report_path(mutant_analysis_dir: Path) -> Path:
    return Path(mutant_analysis_dir, "fail_sars-cov-2_841080_results.csv")


@pytest.fixture(name="passing_report_path")
def passing_report_path(mutant_analysis_dir: Path) -> Path:
    return Path(mutant_analysis_dir, "pass_sars-cov-2_208455_results.csv")


@pytest.fixture(name="mutant_store")
def mutant_store(store: Store, helpers: StoreHelpers) -> Store:
    # Add mutant application and application_version
    application = helpers.add_application(
        store=store, application_tag="VWGDPTR001", target_reads=2000000, percent_reads_guaranteed=1
    )

    # Add cases
    case_qc_pass = helpers.add_case(store=store, name="mutant_case_qc_pass")
    case_qc_fail = helpers.add_case(store=store, name="mutant_case_qc_fail")

    # Add samples
    sample_qc_pass = helpers.add_sample(
        store=store,
        internal_id="ACC0000A1",
        name="23CS503186",
        control=ControlOptions.EMPTY,
        reads=861966,
        application_version=application,
    )

    sample_qc_fail = helpers.add_sample(
        store=store,
        internal_id="ACC0000A2",
        name="23CS102408",
        control=ControlOptions.EMPTY,
        reads=438776,
        application_version=application,
    )

    external_negative_control_qc_pass = helpers.add_sample(
        store=store,
        internal_id="ACC0000A3",
        name="0PROVSEK",
        control=ControlOptions.NEGATIVE,
        reads=20674,
        application_version=application,
    )

    internal_negative_control_qc_pass = helpers.add_sample(
        store=store,
        internal_id="ACC0000A4",
        name="NTC-CG-10",
        control=ControlOptions.NEGATIVE,
        reads=0,
        application_version=application,
    )

    # Add CaseSample relationships
    # case_qc_pass
    helpers.add_relationship(case=case_qc_pass, sample=sample_qc_pass)
    helpers.add_relationship(case=case_qc_pass, sample=external_negative_control_qc_pass)

    # case_qc_fail
    helpers.add_relationship(case=case_qc_fail, sample=sample_qc_fail)
    helpers.add_relationship(case=case_qc_pass, sample=external_negative_control_qc_pass)

    # TODO: Set up case with internal negative control failing qc
    # case_qc_fail_for_internal_control = helpers.add_case(store=store, name="case_qc_fail_for_internal_control")
    # internal_negative_control_qc_fail = helpers.add_sample(
    #     store=store,
    #     internal_id="ACC0000A4",
    #     name="NTC-CG-11",
    #     control=ControlOptions.NEGATIVE,
    #     reads=3000,
    #     application_version=application,
    # )

    return store
