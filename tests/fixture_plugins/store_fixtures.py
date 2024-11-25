from typing import Generator

import pytest

from cg.constants.constants import ControlOptions
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def applications_store(store: Store, helpers: StoreHelpers) -> Store:
    """Return a store populated with applications from excel file"""
    app_tags: list[str] = ["PGOTTTR020", "PGOTTTR030", "PGOTTTR040"]
    for app_tag in app_tags:
        helpers.ensure_application(store=store, tag=app_tag)
    return store


@pytest.fixture
def microbial_store(store: Store, helpers: StoreHelpers) -> Generator[Store, None, None]:
    """Populate a store with microbial application tags"""
    microbial_active_apptags = ["MWRNXTR003", "MWGNXTR003", "MWMNXTR003", "MWLNXTR003"]
    microbial_inactive_apptags = ["MWXNXTR003", "VWGNXTR001", "VWLNXTR001"]

    for app_tag in microbial_active_apptags:
        helpers.ensure_application(store=store, tag=app_tag, prep_category="mic", is_archived=False)

    for app_tag in microbial_inactive_apptags:
        helpers.ensure_application(store=store, tag=app_tag, prep_category="mic", is_archived=True)

    return store


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
