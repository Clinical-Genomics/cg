import datetime as dt

import pytest

from cg.constants import Pipeline
from cg.constants.constants import CustomerId, PrepCategory
from cg.constants.subject import PhenotypeStatus
from cg.store import Store
from cg.store.models import CaseSample
from tests.meta.demultiplex.conftest import populated_flow_cell_store
from tests.store_helpers import StoreHelpers


@pytest.fixture(name="microbial_store")
def microbial_store(store: Store, helpers: StoreHelpers) -> Store:
    """Populate a store with microbial application tags"""
    microbial_active_apptags = ["MWRNXTR003", "MWGNXTR003", "MWMNXTR003", "MWLNXTR003"]
    microbial_inactive_apptags = ["MWXNXTR003", "VWGNXTR001", "VWLNXTR001"]

    for app_tag in microbial_active_apptags:
        helpers.ensure_application(store=store, tag=app_tag, prep_category="mic", is_archived=False)

    for app_tag in microbial_inactive_apptags:
        helpers.ensure_application(store=store, tag=app_tag, prep_category="mic", is_archived=True)

    return store


@pytest.fixture(name="re_sequenced_sample_store")
def re_sequenced_sample_store(
    store: Store,
    bcl_convert_flow_cell_id: str,
    case_id: str,
    family_name: str,
    bcl2fastq_flow_cell_id: str,
    sample_id: str,
    ticket_id: str,
    timestamp_now: dt.datetime,
    helpers,
) -> Store:
    """Populate a store with a Fluffy case, with a sample that has been sequenced on two flow cells."""
    re_sequenced_sample_store: Store = store
    store_case = helpers.add_case(
        store=re_sequenced_sample_store,
        internal_id=case_id,
        name=family_name,
        data_analysis=Pipeline.FLUFFY,
    )

    store_sample = helpers.add_sample(
        store=re_sequenced_sample_store,
        application_type=PrepCategory.READY_MADE_LIBRARY.value,
        is_tumour=False,
        internal_id=sample_id,
        reads=1200000000,
        original_ticket=ticket_id,
        last_sequenced_at=timestamp_now,
    )

    one_day_ahead_of_now = timestamp_now + dt.timedelta(days=1)

    helpers.add_flow_cell(
        store=re_sequenced_sample_store,
        flow_cell_name=bcl_convert_flow_cell_id,
        samples=[store_sample],
        date=timestamp_now,
    )

    helpers.add_flow_cell(
        store=re_sequenced_sample_store,
        flow_cell_name=bcl2fastq_flow_cell_id,
        samples=[store_sample],
        date=one_day_ahead_of_now,
    )

    helpers.add_relationship(store=re_sequenced_sample_store, case=store_case, sample=store_sample)
    helpers.add_sample_lane_sequencing_metrics(
        store=re_sequenced_sample_store,
        sample_internal_id=store_sample.internal_id,
        flow_cell_name=bcl2fastq_flow_cell_id,
        flow_cell_lane_number=1,
        sample_total_reads_in_lane=120000000,
        sample_base_percentage_passing_q30=90,
    )
    return re_sequenced_sample_store


@pytest.fixture(name="max_nr_of_cases")
def max_nr_of_cases() -> int:
    """Return the number of maximum number of cases"""
    return 50


@pytest.fixture(name="store_failing_sequencing_qc")
def store_failing_sequencing_qc(
    bcl2fastq_flow_cell_id: str,
    sample_id: str,
    ticket_id: str,
    timestamp_now: dt.datetime,
    helpers,
    store: Store,
) -> Store:
    """Populate a store with a Fluffy case, with a sample that has been sequenced on two flow cells."""
    store_case = helpers.add_case(
        store=store,
        internal_id="fluffy_case",
        name="fluffy_case",
        data_analysis=Pipeline.FLUFFY,
    )

    store_sample = helpers.add_sample(
        store=store,
        application_type=PrepCategory.READY_MADE_LIBRARY.value,
        customer_id="fluffy_customer",
        is_tumour=False,
        internal_id="fluffy_sample",
        reads=5,
        original_ticket=ticket_id,
        last_sequenced_at=timestamp_now,
    )

    helpers.add_flow_cell(
        store=store,
        flow_cell_name=bcl2fastq_flow_cell_id,
        samples=[store_sample],
        date=timestamp_now,
    )

    helpers.add_relationship(store=store, case=store_case, sample=store_sample)
    helpers.add_sample_lane_sequencing_metrics(
        store=store,
        sample_internal_id=store_sample.internal_id,
        flow_cell_name=bcl2fastq_flow_cell_id,
        flow_cell_lane_number=1,
        sample_total_reads_in_lane=5,
        sample_base_percentage_passing_q30=30,
    )
    return store


@pytest.fixture(name="max_nr_of_samples")
def max_nr_of_samples() -> int:
    """Return the number of maximum number of samples"""
    return 50


@pytest.fixture(name="EXPECTED_NUMBER_OF_NOT_ARCHIVED_APPLICATIONS")
def expected_number_of_not_archived_applications() -> int:
    """Return the number of expected number of not archived applications"""
    return 4


@pytest.fixture(name="EXPECTED_NUMBER_OF_APPLICATIONS")
def expected_number_of_applications() -> int:
    """Return the number of expected number of applications with prep category"""
    return 7


@pytest.fixture(name="store_with_samples_that_have_names")
def store_with_samples_that_have_names(store: Store, helpers: StoreHelpers) -> Store:
    """Return a store with two samples of which one has a name"""
    for index in range(1, 4):
        helpers.add_sample(
            store=store, internal_id=f"test_sample_{index}", name=f"test_sample_{index}"
        )

    helpers.add_sample(
        store=store,
        customer_id="unrelated_customer",
        internal_id="unrelated_id",
        name="unrelated_name",
    )
    return store


@pytest.fixture(name="cust123")
def cust123() -> str:
    """Return a customer id"""
    return "cust123"


@pytest.fixture(name="test_subject")
def test_subject() -> str:
    """Return a subject id"""
    return "test_subject"


@pytest.fixture(name="store_with_samples_subject_id_and_tumour_status")
def store_with_samples_subject_id_and_tumour_status(
    store: Store,
    helpers: StoreHelpers,
    cust123: str,
    test_subject: str,
) -> Store:
    """Return a store with two samples that have subject ids of which one is tumour"""
    helpers.add_sample(
        store=store,
        customer_id=cust123,
        is_tumour=True,
        internal_id="test_sample_1",
        name="sample_1",
        subject_id=test_subject,
    )

    helpers.add_sample(
        store=store,
        customer_id=cust123,
        is_tumour=False,
        internal_id="test_sample_2",
        name="sample_2",
        subject_id=test_subject,
    )
    return store


@pytest.fixture(name="store_with_samples_and_tumour_status_missing_subject_id")
def store_with_samples_and_tumour_status_missing_subject_id(
    store: Store,
    helpers: StoreHelpers,
    cust123: str,
    test_subject: str,
) -> Store:
    """Return a store with two samples of which one is tumour"""
    helpers.add_sample(
        store=store,
        customer_id=cust123,
        is_tumour=True,
        internal_id="test_sample_1",
        name="sample_1",
    )

    helpers.add_sample(
        store=store,
        customer_id=cust123,
        is_tumour=False,
        internal_id="test_sample_2",
        name="sample_2",
    )
    return store


@pytest.fixture(name="store_with_samples_customer_id_and_subject_id_and_tumour_status")
def store_with_samples_customer_id_and_subject_id_and_tumour_status(
    store: Store, helpers: StoreHelpers
) -> Store:
    """Return a store with four samples with different customer IDs, and tumour status."""
    samples_data = [
        # customer_id, subject_id, is_tumour
        ("1", "test_subject", True),
        ("1", "test_subject_2", False),
        ("2", "test_subject", True),
        ("2", "test_subject_2", False),
    ]
    for customer_id, subject_id, is_tumour in samples_data:
        helpers.add_sample(
            store=store,
            customer_id=customer_id,
            is_tumour=is_tumour,
            internal_id=f"test_sample_{customer_id}_{subject_id}",
            name=f"sample_{customer_id}_{subject_id}",
            subject_id=subject_id,
        )
    return store


@pytest.fixture(name="pool_name_1")
def pool_name_1() -> str:
    """Return the name of the first pool."""
    return "pool_1"


@pytest.fixture(name="pool_order_1")
def pool_order_1() -> str:
    """Return the order of the first pool."""
    return "pool_order_1"


@pytest.fixture(name="store_with_multiple_pools_for_customer")
def store_with_multiple_pools_for_customer(
    store: Store,
    helpers: StoreHelpers,
    customer_id: str = CustomerId.CUST132,
) -> Store:
    """Return a store with two pools with different names for the same customer."""
    for number in range(2):
        helpers.ensure_pool(
            store=store,
            customer_id=customer_id,
            name="_".join(["pool", str(number)]),
            order="_".join(["pool", "order", str(number)]),
        )
    yield store


@pytest.fixture(name="store_with_active_sample_analyze")
def store_with_active_sample_analyze(store: Store, helpers: StoreHelpers) -> Store:
    """Return a store with an active sample with action analyze."""
    # GIVEN a store with a sample that is active
    case = helpers.add_case(
        store=store, name="test_case", internal_id="test_case_internal_id", action="analyze"
    )
    sample = helpers.add_sample(
        store=store, internal_id="test_sample_internal_id", name="test_sample"
    )
    helpers.add_relationship(store=store, sample=sample, case=case)

    yield store


@pytest.fixture(name="store_with_active_sample_running")
def store_with_active_sample_running(store: Store, helpers: StoreHelpers) -> Store:
    """Return a store with an active sample with action running."""
    # GIVEN a store with a sample that is active
    case = helpers.add_case(
        store=store, name="test_case", internal_id="test_case_internal_id", action="running"
    )
    sample = helpers.add_sample(
        store=store, internal_id="test_sample_internal_id", name="test_sample"
    )
    helpers.add_relationship(store=store, sample=sample, case=case)

    yield store


@pytest.fixture(name="three_customer_ids")
def three_customer_ids() -> list[str]:
    """Return three customer ids."""
    yield ["".join(["cust00", str(number)]) for number in range(3)]


@pytest.fixture(name="three_pool_names")
def three_pool_names() -> list[str]:
    """Return three customer ids."""
    yield ["_".join(["test_pool", str(number)]) for number in range(3)]


@pytest.fixture(name="store_with_samples_for_multiple_customers")
def store_with_samples_for_multiple_customers(
    store: Store, helpers: StoreHelpers, timestamp_now: dt.datetime
) -> Store:
    """Return a store with two samples for three different customers."""
    for number in range(3):
        helpers.add_sample(
            store=store,
            customer_id="".join(["cust00", str(number)]),
            internal_id="_".join(["test_sample", str(number)]),
            no_invoice=False,
            delivered_at=timestamp_now,
        )
    yield store


@pytest.fixture(name="store_with_pools_for_multiple_customers")
def store_with_pools_for_multiple_customers(
    store: Store, helpers: StoreHelpers, timestamp_now: dt.datetime
) -> Store:
    """Return a store with two samples for three different customers."""
    for number in range(3):
        helpers.ensure_pool(
            store=store,
            name="_".join(["test_pool", str(number)]),
            customer_id="".join(["cust00", str(number)]),
            no_invoice=False,
            delivered_at=timestamp_now,
        )
    yield store


@pytest.fixture(name="store_with_analyses_for_cases")
def store_with_analyses_for_cases(
    analysis_store: Store,
    helpers: StoreHelpers,
    timestamp_now: dt.datetime,
    timestamp_yesterday: dt.datetime,
) -> Store:
    """Return a store with two analyses for two cases."""
    case_one = analysis_store.get_case_by_internal_id("yellowhog")
    case_two = helpers.add_case(analysis_store, internal_id="test_case_1")

    cases = [case_one, case_two]
    for case in cases:
        oldest_analysis = helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_yesterday,
            uploaded_at=timestamp_yesterday,
            delivery_reported_at=None,
            completed_at=timestamp_yesterday,
        )
        helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_now,
            uploaded_at=timestamp_now,
            delivery_reported_at=None,
            completed_at=timestamp_now,
        )
        sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
        link: CaseSample = analysis_store.relate_sample(
            case=oldest_analysis.case, sample=sample, status=PhenotypeStatus.UNKNOWN
        )
        analysis_store.session.add(link)

    return analysis_store


@pytest.fixture(name="store_with_analyses_for_cases_not_uploaded_fluffy")
def store_with_analyses_for_cases_not_uploaded_fluffy(
    analysis_store: Store,
    helpers: StoreHelpers,
    timestamp_now: dt.datetime,
    timestamp_yesterday: dt.datetime,
) -> Store:
    """Return a store with two analyses for two cases and pipeline."""
    case_one = analysis_store.get_case_by_internal_id("yellowhog")
    case_two = helpers.add_case(analysis_store, internal_id="test_case_1")

    cases = [case_one, case_two]
    for case in cases:
        oldest_analysis = helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_yesterday,
            uploaded_at=timestamp_yesterday,
            delivery_reported_at=None,
            pipeline=Pipeline.FLUFFY,
        )
        helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_now,
            uploaded_at=None,
            delivery_reported_at=None,
            pipeline=Pipeline.FLUFFY,
        )
        sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
        link: CaseSample = analysis_store.relate_sample(
            case=oldest_analysis.case, sample=sample, status=PhenotypeStatus.UNKNOWN
        )
        analysis_store.session.add(link)
    return analysis_store


@pytest.fixture(name="store_with_analyses_for_cases_not_uploaded_microsalt")
def store_with_analyses_for_cases_not_uploaded_microsalt(
    analysis_store: Store,
    helpers: StoreHelpers,
    timestamp_now: dt.datetime,
    timestamp_yesterday: dt.datetime,
) -> Store:
    """Return a store with two analyses for two cases and pipeline."""

    case_one = analysis_store.get_case_by_internal_id("yellowhog")
    case_two = helpers.add_case(analysis_store, internal_id="test_case_1")

    cases = [case_one, case_two]
    for case in cases:
        oldest_analysis = helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_yesterday,
            uploaded_at=timestamp_yesterday,
            delivery_reported_at=None,
            pipeline=Pipeline.MICROSALT,
        )
        helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_now,
            uploaded_at=None,
            delivery_reported_at=None,
            pipeline=Pipeline.MICROSALT,
        )
        sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
        link: CaseSample = analysis_store.relate_sample(
            case=oldest_analysis.case, sample=sample, status=PhenotypeStatus.UNKNOWN
        )
        analysis_store.session.add(link)
    return analysis_store


@pytest.fixture(name="store_with_analyses_for_cases_to_deliver")
def store_with_analyses_for_cases_to_deliver(
    analysis_store: Store,
    helpers: StoreHelpers,
    timestamp_now: dt.datetime,
    timestamp_yesterday: dt.datetime,
) -> Store:
    """Return a store with two analyses for two cases."""
    case_one = analysis_store.get_case_by_internal_id("yellowhog")
    case_two = helpers.add_case(analysis_store, internal_id="test_case_1")

    cases = [case_one, case_two]
    for case in cases:
        oldest_analysis = helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_yesterday,
            uploaded_at=None,
            delivery_reported_at=None,
            completed_at=timestamp_yesterday,
            pipeline=Pipeline.FLUFFY,
        )
        helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_now,
            uploaded_at=None,
            delivery_reported_at=None,
            completed_at=timestamp_now,
            pipeline=Pipeline.MIP_DNA,
        )
        sample = helpers.add_sample(analysis_store, delivered_at=None)
        link: CaseSample = analysis_store.relate_sample(
            case=oldest_analysis.case, sample=sample, status=PhenotypeStatus.UNKNOWN
        )
        analysis_store.session.add(link)

    return analysis_store
