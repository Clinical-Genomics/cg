import datetime as dt
import pytest

from typing import Iterable, List
from cg.constants import Pipeline
from cg.constants.constants import PrepCategory
from cg.constants.priority import PriorityTerms
from cg.meta.orders.pool_submitter import PoolSubmitter
from cg.store import Store
from cg.store.api.import_func import (
    parse_application_versions,
    parse_applications,
    versions_are_same,
)
from cg.store.api.models import ApplicationSchema, ApplicationVersionSchema
from tests.store_helpers import StoreHelpers
from cg.store.models import ApplicationVersion, Pool, Sample, Invoice, Application
from tests.meta.demultiplex.conftest import fixture_populated_flow_cell_store
from cg.constants.invoice import CustomerNames


class StoreCheckers:
    @staticmethod
    def get_versions_from_store(store: Store, application_tag: str) -> List[ApplicationVersion]:
        """Gets all versions for the specified application"""

        return store.get_application_by_tag(tag=application_tag).versions

    @staticmethod
    def get_application_from_store(store: Store, application_tag: str) -> Application:
        """Gets the specified application"""

        return store.get_application_by_tag(tag=application_tag)

    @staticmethod
    def version_exists_in_store(store: Store, application: ApplicationVersionSchema):
        """Check if the given raw version exists in the store."""
        db_versions: List[Application] = StoreCheckers.get_versions_from_store(
            store=store, application_tag=application.app_tag
        )
        return any(
            versions_are_same(version_obj=db_version, application_version=application)
            for db_version in db_versions
        )

    @staticmethod
    def all_versions_exist_in_store(store: Store, excel_path: str):
        """Check if all versions in the Excel exists in the store."""
        applications: Iterable[ApplicationVersionSchema] = parse_application_versions(
            excel_path=excel_path
        )
        return all(
            StoreCheckers.version_exists_in_store(store=store, application=application)
            for application in applications
        )

    @staticmethod
    def all_applications_exists(store: Store, applications_file: str):
        """Check if all applications in the Excel exists in the store."""
        applications: Iterable[ApplicationSchema] = parse_applications(excel_path=applications_file)
        return all(
            StoreCheckers.exists_application_in_store(store=store, application_tag=application.tag)
            for application in applications
        )

    @staticmethod
    def exists_application_in_store(store: Store, application_tag: str):
        """Check if the given raw application exists in the store"""
        db_application = StoreCheckers.get_application_from_store(
            store=store, application_tag=application_tag
        )

        return db_application is not None


@pytest.fixture(name="store_checkers")
def fixture_store_checkers() -> StoreCheckers:
    return StoreCheckers()


@pytest.fixture(name="applications_store")
def fixture_applications_store(
    store: Store, application_versions_file: str, helpers: StoreHelpers
) -> Store:
    """Return a store populated with applications from excel file"""
    versions: Iterable[ApplicationVersionSchema] = parse_application_versions(
        excel_path=application_versions_file
    )

    for version in versions:
        helpers.ensure_application(store=store, tag=version.app_tag)

    return store


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


@pytest.fixture(name="microbial_store_dummy_tag")
def fixture_microbial_store_dummy_tag(microbial_store: Store, helpers: StoreHelpers) -> Store:
    """Populate a microbial store with a extra dummy app tag"""
    helpers.ensure_application(
        store=microbial_store, tag="dummy_tag", prep_category="mic", is_archived=False
    )
    return microbial_store


@pytest.fixture(name="rml_store")
def fixture_rml_store(store: Store, helpers: StoreHelpers) -> Store:
    """Populate a store with microbial application tags"""
    active_apptags = [
        "RMLP10R300",
        "RMLP10S130",
        "RMLP15R100",
        "RMLP15R200",
        "RMLP15R400",
        "RMLP15R500",
        "RMLP15R750",
        "RMLP15R825",
        "RMLP15S100",
        "RMLP15S125",
        "RMLP15S150",
        "RMLP15S175",
        "RMLP15S200",
        "RMLP15S225",
        "RMLP15S425",
    ]
    inactive_apptags = [
        "RMLP05R800",
        "RMLP15S250",
        "RMLP15S275",
        "RMLP15S300",
        "RMLP15S325",
        "RMLP15S350",
        "RMLP15S375",
        "RMLP15S400",
        "RMLP15S450",
        "RMLP15S475",
        "RMLP15S500",
        "RMLS05R200",
        "RMLCUSR800",
        "RMLCUSS160",
    ]

    for app_tag in active_apptags:
        helpers.ensure_application(store=store, tag=app_tag, prep_category="rml", is_archived=False)

    for app_tag in inactive_apptags:
        helpers.ensure_application(store=store, tag=app_tag, prep_category="rml", is_archived=True)

    return store


@pytest.fixture(name="rml_pool_store")
def fixture_rml_pool_store(
    case_id: str,
    customer_id: str,
    helpers,
    sample_id: str,
    store: Store,
    ticket: str,
    timestamp_now: dt.datetime,
):
    new_customer = store.add_customer(
        internal_id=customer_id,
        name="Test customer",
        scout_access=True,
        invoice_address="skolgatan 15",
        invoice_reference="abc",
    )
    store.add_commit(new_customer)

    application = store.add_application(
        tag="RMLP05R800",
        prep_category="rml",
        description="Ready-made",
        percent_kth=80,
        percent_reads_guaranteed=75,
        sequencing_depth=0,
        target_reads=800,
    )
    store.add_commit(application)

    app_version = store.add_version(
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
    store.add_commit(app_version)

    new_pool = store.add_pool(
        customer=new_customer,
        name="Test",
        order="Test",
        ordered=dt.datetime.now(),
        application_version=app_version,
    )
    store.add_commit(new_pool)
    new_case = helpers.add_case(
        store=store,
        internal_id=case_id,
        name=PoolSubmitter.create_case_name(ticket=ticket, pool_name="Test"),
    )
    store.add_commit(new_case)

    new_sample = helpers.add_sample(
        store=store,
        internal_id=sample_id,
        application_tag=application.tag,
        application_type=application.prep_category,
        customer_id=new_customer.id,
    )
    new_sample.application_version = app_version
    store.add_commit(new_sample)

    helpers.add_relationship(
        store=store,
        sample=new_sample,
        case=new_case,
    )

    yield store


@pytest.fixture(name="re_sequenced_sample_store")
def fixture_re_sequenced_sample_store(
    store: Store,
    another_flow_cell_id: str,
    case_id: str,
    family_name: str,
    flow_cell_id: str,
    sample_id: str,
    ticket: str,
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
        original_ticket=ticket,
        sequenced_at=timestamp_now,
    )

    one_day_ahead_of_now = timestamp_now + dt.timedelta(days=1)

    helpers.add_flowcell(
        store=re_sequenced_sample_store,
        flow_cell_id=another_flow_cell_id,
        samples=[store_sample],
        date=timestamp_now,
    )

    helpers.add_flowcell(
        store=re_sequenced_sample_store,
        flow_cell_id=flow_cell_id,
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


@pytest.fixture(name="EXPECTED_NUMBER_OF_APPLICATIONS_WITH_PREP_CATEGORY")
def fixture_expected_number_of_applications_with_prep_category() -> int:
    """Return the number of expected number of applications with prep category"""
    return 7


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

    helpers.add_sample(store=store, internal_id="unrelated_id", name="unrelated_name")
    return store


@pytest.fixture(name="store_with_samples_subject_id_and_tumour_status")
def store_with_samples_subject_id_and_tumour_status(
    store: Store,
    helpers: StoreHelpers,
    customer_id: str = "cust123",
    subject_id: str = "test_subject",
) -> Store:
    """Return a store with two samples that have subject ids of which one is tumour"""
    helpers.add_sample(
        store=store,
        internal_id="test_sample_1",
        name="sample_1",
        subject_id=subject_id,
        is_tumour=True,
        customer_id=customer_id,
    )

    helpers.add_sample(
        store=store,
        internal_id="test_sample_2",
        name="sample_2",
        subject_id=subject_id,
        is_tumour=False,
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
