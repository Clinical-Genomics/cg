from datetime import datetime, timedelta
from typing import Generator
import pytest
from cg.constants import Workflow
from cg.constants.constants import CustomerId, PrepCategory
from cg.constants.subject import PhenotypeStatus
from cg.store.models import CaseSample, Order
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def cust123() -> str:
    """Return a customer id"""
    return "cust123"


@pytest.fixture
def test_subject() -> str:
    """Return a subject id"""
    return "test_subject"


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
def store_with_active_sample_analyze(
    store: Store, helpers: StoreHelpers
) -> Generator[Store, None, None]:
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


@pytest.fixture
def store_with_active_sample_running(
    store: Store, helpers: StoreHelpers
) -> Generator[Store, None, None]:
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


@pytest.fixture
def store_with_analyses_for_cases_not_uploaded_microsalt(
    analysis_store: Store,
    helpers: StoreHelpers,
    timestamp_now: datetime,
    timestamp_yesterday: datetime,
) -> Store:
    """Return a store with two analyses for two cases and workflow."""

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
            workflow=Workflow.MICROSALT,
        )
        helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_now,
            uploaded_at=None,
            delivery_reported_at=None,
            workflow=Workflow.MICROSALT,
        )
        sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
        link: CaseSample = analysis_store.relate_sample(
            case=oldest_analysis.case, sample=sample, status=PhenotypeStatus.UNKNOWN
        )
        analysis_store.session.add(link)
    return analysis_store


@pytest.fixture
def store_with_analyses_for_cases_to_deliver(
    analysis_store: Store,
    helpers: StoreHelpers,
    timestamp_now: datetime,
    timestamp_yesterday: datetime,
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
            completed_at=timestamp_yesterday,
            uploaded_at=None,
            delivery_reported_at=None,
            workflow=Workflow.FLUFFY,
        )
        helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_now,
            completed_at=timestamp_now,
            uploaded_at=None,
            delivery_reported_at=None,
            workflow=Workflow.MIP_DNA,
        )
        sample = helpers.add_sample(analysis_store, delivered_at=None)
        link: CaseSample = analysis_store.relate_sample(
            case=oldest_analysis.case, sample=sample, status=PhenotypeStatus.UNKNOWN
        )
        analysis_store.session.add(link)

    return analysis_store


@pytest.fixture
def store_with_multiple_pools_for_customer(
    store: Store,
    helpers: StoreHelpers,
    customer_id: str = CustomerId.CUST132,
) -> Generator[Store, None, None]:
    """Return a store with two pools with different names for the same customer."""
    for number in range(2):
        helpers.ensure_pool(
            store=store,
            customer_id=customer_id,
            name="_".join(["pool", str(number)]),
            order="_".join(["pool", "order", str(number)]),
        )
    yield store


@pytest.fixture
def re_sequenced_sample_store(
    store: Store,
    novaseq_6000_post_1_5_kits_flow_cell_id: str,
    case_id: str,
    family_name: str,
    novaseq_6000_pre_1_5_kits_flow_cell_id: str,
    sample_id: str,
    ticket_id: str,
    timestamp_now: datetime,
    helpers,
) -> Store:
    """Populate a store with a Fluffy case, with a sample that has been sequenced on two flow cells."""
    re_sequenced_sample_store: Store = store
    store_case = helpers.add_case(
        store=re_sequenced_sample_store,
        internal_id=case_id,
        name=family_name,
        data_analysis=Workflow.FLUFFY,
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

    one_day_ahead_of_now = timestamp_now + timedelta(days=1)

    helpers.add_flow_cell(
        store=re_sequenced_sample_store,
        flow_cell_name=novaseq_6000_post_1_5_kits_flow_cell_id,
        samples=[store_sample],
        date=timestamp_now,
    )

    helpers.add_flow_cell(
        store=re_sequenced_sample_store,
        flow_cell_name=novaseq_6000_pre_1_5_kits_flow_cell_id,
        samples=[store_sample],
        date=one_day_ahead_of_now,
    )

    helpers.add_relationship(store=re_sequenced_sample_store, case=store_case, sample=store_sample)
    helpers.ensure_sample_lane_sequencing_metrics(
        store=re_sequenced_sample_store,
        sample_internal_id=store_sample.internal_id,
        flow_cell_name=novaseq_6000_pre_1_5_kits_flow_cell_id,
        flow_cell_lane_number=1,
        sample_total_reads_in_lane=120000000,
        sample_base_percentage_passing_q30=90,
    )
    return re_sequenced_sample_store


@pytest.fixture
def pool_name_1() -> str:
    """Return the name of the first pool."""
    return "pool_1"


@pytest.fixture
def pool_order_1() -> str:
    """Return the order of the first pool."""
    return "pool_order_1"


@pytest.fixture
def expected_number_of_not_archived_applications() -> int:
    """Return the number of expected numbers of not archived applications"""
    return 4


@pytest.fixture
def expected_number_of_applications() -> int:
    """Return the number of expected number of applications with prep category"""
    return 7


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
def max_nr_of_samples() -> int:
    """Return maximum numbers of samples"""
    return 50


@pytest.fixture
def max_nr_of_cases() -> int:
    """Return maximum numbers of cases"""
    return 50


@pytest.fixture
def three_customer_ids() -> list[str]:
    """Return three customer ids."""
    yield ["".join(["cust00", str(number)]) for number in range(3)]


@pytest.fixture
def store_with_pools_for_multiple_customers(
    store: Store, helpers: StoreHelpers, timestamp_now: datetime
) -> Generator[Store, None, None]:
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


@pytest.fixture
def three_pool_names() -> list[str]:
    """Return three customer ids."""
    yield ["_".join(["test_pool", str(number)]) for number in range(3)]


@pytest.fixture
def order(helpers: StoreHelpers, store: Store) -> Order:
    order: Order = helpers.add_order(
        store=store, customer_id=1, ticket_id=1, order_date=datetime.now()
    )
    return order


@pytest.fixture
def order_another(helpers: StoreHelpers, store: Store) -> Order:
    order: Order = helpers.add_order(
        store=store, customer_id=2, ticket_id=2, order_date=datetime.now()
    )
    return order


@pytest.fixture
def order_balsamic(helpers: StoreHelpers, store: Store) -> Order:
    order: Order = helpers.add_order(
        store=store,
        customer_id=2,
        ticket_id=3,
        order_date=datetime.now(),
        workflow=Workflow.BALSAMIC,
    )
    return order
