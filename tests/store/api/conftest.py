import datetime as dt
import pytest

from typing import Iterable, List

from cg.constants import Pipeline
from cg.constants.constants import PrepCategory
from cg.constants.priority import PriorityTerms
from cg.meta.orders.pool_submitter import PoolSubmitter
from cg.store import Store, models
from cg.store.api.import_func import (
    parse_application_versions,
    parse_applications,
    versions_are_same,
)
from cg.store.api.models import ApplicationSchema, ApplicationVersionSchema
from tests.store_helpers import StoreHelpers
from tests.meta.demultiplex.conftest import fixture_populated_flow_cell_store


class StoreCheckers:
    @staticmethod
    def get_versions_from_store(
        store: Store, application_tag: str
    ) -> List[models.ApplicationVersion]:
        """Gets all versions for the specified application"""

        return store.application(application_tag).versions

    @staticmethod
    def get_application_from_store(store: Store, application_tag: str) -> models.Application:
        """Gets the specified application"""

        return store.application(application_tag)

    @staticmethod
    def version_exists_in_store(store: Store, application: ApplicationVersionSchema):
        """Check if the given raw version exists in the store."""
        db_versions: List[models.Application] = StoreCheckers.get_versions_from_store(
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
        helpers.ensure_application(
            store=store, tag=app_tag, application_type="mic", is_archived=False
        )

    for app_tag in microbial_inactive_apptags:
        helpers.ensure_application(
            store=store, tag=app_tag, application_type="mic", is_archived=True
        )

    return store


@pytest.fixture(name="microbial_store_dummy_tag")
def fixture_microbial_store_dummy_tag(microbial_store: Store, helpers: StoreHelpers) -> Store:
    """Populate a microbial store with a extra dummy app tag"""
    helpers.ensure_application(
        store=microbial_store, tag="dummy_tag", application_type="mic", is_archived=False
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
        helpers.ensure_application(
            store=store, tag=app_tag, application_type="rml", is_archived=False
        )

    for app_tag in inactive_apptags:
        helpers.ensure_application(
            store=store, tag=app_tag, application_type="rml", is_archived=True
        )

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
        category="rml",
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
