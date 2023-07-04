import datetime as dt
import pytest

from typing import List
from cg.constants.constants import PrepCategory
from cg.constants.priority import PriorityTerms
from cg.meta.orders.pool_submitter import PoolSubmitter
from cg.store import Store
from tests.meta.demultiplex.conftest import fixture_populated_flow_cell_store
from tests.store_helpers import StoreHelpers
from cg.constants.invoice import CustomerNames
from cg.constants.subject import PhenotypeStatus
from cg.constants import Pipeline


@pytest.fixture(name="microbial_store")
def fixture_microbial_store(store: Store, helpers: StoreHelpers) -> Store:
    """Populate a store with microbial application tags"""
    microbial_active_apptags = ["MWRNXTR003", "MWGNXTR003", "MWMNXTR003", "MWLNXTR003"]
    microbial_inactive_apptags = ["MWXNXTR003", "VWGNXTR001", "VWLNXTR001"]

    for app_tag in microbial_active_apptags:
        helpers.ensure_application(store=store, tag=app_tag, prep_category="mic", is_archived=False)

    for app_tag in microbial_inactive_apptags:
        helpers.ensure_application(store=store, tag=app_tag, prep_category="mic", is_archived=True)

    return store


@pytest.fixture(name="rml_pool_store")
def fixture_rml_pool_store(
    case_id: str,
    customer_id: str,
    helpers,
    sample_id: str,
    store: Store,
    ticket_id: str,
    timestamp_now: dt.datetime,
):
    new_customer = store.add_customer(
        internal_id=customer_id,
        name="Test customer",
        scout_access=True,
        invoice_address="skolgatan 15",
        invoice_reference="abc",
    )
    store.session.add(new_customer)

    application = store.add_application(
        tag="RMLP05R800",
        prep_category="rml",
        description="Ready-made",
        percent_kth=80,
        percent_reads_guaranteed=75,
        sequencing_depth=0,
        target_reads=800,
    )
    store.session.add(application)

    app_version = store.add_application_version(
        application=application,
        version=1,
        valid_from=timestamp_now,
        prices={
            PriorityTerms.STANDARD: 12,
            PriorityTerms.PRIORITY: 222,
            PriorityTerms.EXPRESS: 123,
            PriorityTerms.RESEARCH: 12,
        },
    )
    store.session.add(app_version)

    new_pool = store.add_pool(
        customer=new_customer,
        name="Test",
        order="Test",
        ordered=dt.datetime.now(),
        application_version=app_version,
    )
    store.session.add(new_pool)
    new_case = helpers.add_case(
        store=store,
        internal_id=case_id,
        name=PoolSubmitter.create_case_name(ticket=ticket_id, pool_name="Test"),
    )
    store.session.add(new_case)

    new_sample = helpers.add_sample(
        store=store,
        internal_id=sample_id,
        application_tag=application.tag,
        application_type=application.prep_category,
        customer_id=new_customer.id,
    )
    new_sample.application_version = app_version
    store.session.add(new_sample)
    store.session.commit()

    helpers.add_relationship(
        store=store,
        sample=new_sample,
        case=new_case,
    )

    yield store


@pytest.fixture(name="re_sequenced_sample_store")
def fixture_re_sequenced_sample_store(
    store: Store,
    dragen_flow_cell_id: str,
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
        internal_id=sample_id,
        is_tumour=False,
        application_type=PrepCategory.READY_MADE_LIBRARY.value,
        reads=1200000000,
        store=re_sequenced_sample_store,
        original_ticket=ticket_id,
        sequenced_at=timestamp_now,
    )

    one_day_ahead_of_now = timestamp_now + dt.timedelta(days=1)

    helpers.add_flowcell(
        store=re_sequenced_sample_store,
        flow_cell_name=dragen_flow_cell_id,
        samples=[store_sample],
        date=timestamp_now,
    )

    helpers.add_flowcell(
        store=re_sequenced_sample_store,
        flow_cell_name=bcl2fastq_flow_cell_id,
        samples=[store_sample],
        date=one_day_ahead_of_now,
    )

    helpers.add_relationship(store=re_sequenced_sample_store, case=store_case, sample=store_sample)

    return re_sequenced_sample_store


@pytest.fixture(name="max_nr_of_cases")
def fixture_max_nr_of_cases() -> int:
    """Return the number of maximum number of cases"""
    return 50


@pytest.fixture(name="max_nr_of_samples")
def fixture_max_nr_of_samples() -> int:
    """Return the number of maximum number of samples"""
    return 50


@pytest.fixture(name="EXPECTED_NUMBER_OF_NOT_ARCHIVED_APPLICATIONS")
def fixture_expected_number_of_not_archived_applications() -> int:
    """Return the number of expected number of not archived applications"""
    return 4


@pytest.fixture(name="EXPECTED_NUMBER_OF_APPLICATIONS")
def fixture_expected_number_of_applications() -> int:
    """Return the number of expected number of applications with prep category"""
    return 7


@pytest.fixture(name="store_with_samples_that_have_names")
def store_with_samples_that_have_names(
    store: Store, helpers: StoreHelpers, name="sample_1"
) -> Store:
    """Return a store with two samples of which one has a name"""
    for index in range(1, 4):
        helpers.add_sample(
            store=store, internal_id=f"test_sample_{index}", name=f"test_sample_{index}"
        )

    helpers.add_sample(
        store=store,
        internal_id="unrelated_id",
        name="unrelated_name",
        customer_id="unrelated_customer",
    )
    return store


@pytest.fixture(name="cust123")
def fixture_cust123() -> str:
    """Return a customer id"""
    return "cust123"


@pytest.fixture(name="test_subject")
def fixture_test_subject() -> str:
    """Return a subject id"""
    return "test_subject"


@pytest.fixture(name="store_with_samples_subject_id_and_tumour_status")
def fixture_store_with_samples_subject_id_and_tumour_status(
    store: Store,
    helpers: StoreHelpers,
    cust123: str,
    test_subject: str,
) -> Store:
    """Return a store with two samples that have subject ids of which one is tumour"""
    helpers.add_sample(
        store=store,
        internal_id="test_sample_1",
        name="sample_1",
        subject_id=test_subject,
        is_tumour=True,
        customer_id=cust123,
    )

    helpers.add_sample(
        store=store,
        internal_id="test_sample_2",
        name="sample_2",
        subject_id=test_subject,
        is_tumour=False,
        customer_id=cust123,
    )
    return store


@pytest.fixture(name="store_with_samples_and_tumour_status_missing_subject_id")
def fixture_store_with_samples_and_tumour_status_missing_subject_id(
    store: Store,
    helpers: StoreHelpers,
    cust123: str,
    test_subject: str,
) -> Store:
    """Return a store with two samples of which one is tumour"""
    helpers.add_sample(
        store=store,
        internal_id="test_sample_1",
        name="sample_1",
        is_tumour=True,
        customer_id=cust123,
    )

    helpers.add_sample(
        store=store,
        internal_id="test_sample_2",
        name="sample_2",
        is_tumour=False,
        customer_id=cust123,
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
            internal_id=f"test_sample_{customer_id}_{subject_id}",
            name=f"sample_{customer_id}_{subject_id}",
            subject_id=subject_id,
            is_tumour=is_tumour,
            customer_id=customer_id,
        )
    return store


@pytest.fixture(name="pool_name_1")
def fixture_pool_name_1() -> str:
    """Return the name of the first pool."""
    return "pool_1"


@pytest.fixture(name="pool_order_1")
def fixture_pool_order_1() -> str:
    """Return the order of the first pool."""
    return "pool_order_1"


@pytest.fixture(name="store_with_multiple_pools_for_customer")
def fixture_store_with_multiple_pools_for_customer(
    store: Store,
    helpers: StoreHelpers,
    customer_id: str = CustomerNames.cust132,
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
def fixture_store_with_active_sample_analyze(store: Store, helpers: StoreHelpers) -> Store:
    """Return a store with an active sample with action analyze."""
    # GIVEN a store with a sample that is active
    case = helpers.add_case(
        store=store, name="test_case", internal_id="test_case_internal_id", action="analyze"
    )
    sample = helpers.add_sample(
        store=store, name="test_sample", internal_id="test_sample_internal_id"
    )
    helpers.add_relationship(store=store, sample=sample, case=case)

    yield store


@pytest.fixture(name="store_with_active_sample_running")
def fixture_store_with_active_sample_running(store: Store, helpers: StoreHelpers) -> Store:
    """Return a store with an active sample with action running."""
    # GIVEN a store with a sample that is active
    case = helpers.add_case(
        store=store, name="test_case", internal_id="test_case_internal_id", action="running"
    )
    sample = helpers.add_sample(
        store=store, name="test_sample", internal_id="test_sample_internal_id"
    )
    helpers.add_relationship(store=store, sample=sample, case=case)

    yield store


@pytest.fixture(name="three_customer_ids")
def fixture_three_customer_ids() -> List[str]:
    """Return three customer ids."""
    yield ["".join(["cust00", str(number)]) for number in range(3)]


@pytest.fixture(name="three_pool_names")
def fixture_three_pool_names() -> List[str]:
    """Return three customer ids."""
    yield ["_".join(["test_pool", str(number)]) for number in range(3)]


@pytest.fixture(name="store_with_samples_for_multiple_customers")
def fixture_store_with_samples_for_multiple_customers(
    store: Store, helpers: StoreHelpers, timestamp_now: dt.datetime
) -> Store:
    """Return a store with two samples for three different customers."""
    for number in range(3):
        helpers.add_sample(
            store=store,
            internal_id="_".join(["test_sample", str(number)]),
            customer_id="".join(["cust00", str(number)]),
            no_invoice=False,
            delivered_at=timestamp_now,
        )
    yield store


@pytest.fixture(name="store_with_pools_for_multiple_customers")
def fixture_store_with_pools_for_multiple_customers(
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
def fixture_store_with_analyses_for_cases(
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
            uploaded_to_vogue_at=timestamp_yesterday,
            completed_at=timestamp_yesterday,
        )
        helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_now,
            uploaded_at=timestamp_now,
            delivery_reported_at=None,
            uploaded_to_vogue_at=None,
            completed_at=timestamp_now,
        )
        sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
        analysis_store.relate_sample(
            family=oldest_analysis.family, sample=sample, status=PhenotypeStatus.UNKNOWN
        )

    return analysis_store


@pytest.fixture(name="store_with_analyses_for_cases_not_uploaded_fluffy")
def fixture_store_with_analyses_for_cases_not_uploaded_fluffy(
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
            uploaded_to_vogue_at=timestamp_yesterday,
            pipeline=Pipeline.FLUFFY,
        )
        helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_now,
            uploaded_at=None,
            delivery_reported_at=None,
            uploaded_to_vogue_at=timestamp_now,
            pipeline=Pipeline.FLUFFY,
        )
        sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
        analysis_store.relate_sample(
            family=oldest_analysis.family, sample=sample, status=PhenotypeStatus.UNKNOWN
        )
    return analysis_store


@pytest.fixture(name="store_with_analyses_for_cases_not_uploaded_microsalt")
def fixture_store_with_analyses_for_cases_not_uploaded_microsalt(
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
            uploaded_to_vogue_at=timestamp_yesterday,
            pipeline=Pipeline.MICROSALT,
        )
        helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_now,
            uploaded_at=None,
            delivery_reported_at=None,
            uploaded_to_vogue_at=timestamp_now,
            pipeline=Pipeline.MICROSALT,
        )
        sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
        analysis_store.relate_sample(
            family=oldest_analysis.family, sample=sample, status=PhenotypeStatus.UNKNOWN
        )
    return analysis_store


@pytest.fixture(name="store_with_analyses_for_cases_to_deliver")
def fixture_store_with_analyses_for_cases_to_deliver(
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
            uploaded_to_vogue_at=timestamp_yesterday,
            completed_at=timestamp_yesterday,
            pipeline=Pipeline.FLUFFY,
        )
        helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_now,
            uploaded_at=None,
            delivery_reported_at=None,
            uploaded_to_vogue_at=None,
            completed_at=timestamp_now,
            pipeline=Pipeline.MIP_DNA,
        )
        sample = helpers.add_sample(analysis_store, delivered_at=None)
        analysis_store.relate_sample(
            family=oldest_analysis.family, sample=sample, status=PhenotypeStatus.UNKNOWN
        )

    return analysis_store
