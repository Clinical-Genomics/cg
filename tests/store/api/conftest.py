import datetime as dt
import pytest

from typing import Iterable, List

from cg.constants import Pipeline
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
        """Check if the given raw version exists in the store"""
        db_versions: List[models.Application] = StoreCheckers.get_versions_from_store(
            store=store, application_tag=application.app_tag
        )

        for db_version in db_versions:
            if versions_are_same(version_obj=db_version, application_version=application):
                return True

        return False

    @staticmethod
    def all_versions_exist_in_store(store: Store, excel_path: str):
        """Check if all versions in the excel exists in the store"""
        applications: Iterable[ApplicationVersionSchema] = parse_application_versions(
            excel_path=excel_path
        )

        for application in applications:
            if not StoreCheckers.version_exists_in_store(store=store, application=application):
                return False

        return True

    @staticmethod
    def all_applications_exists(store: Store, applications_file: str):
        """Check if all applications in the excel exists in the store"""
        applications: Iterable[ApplicationSchema] = parse_applications(excel_path=applications_file)

        for application in applications:
            if not StoreCheckers.exists_application_in_store(
                store=store, application_tag=application.tag
            ):
                return False

        return True

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


@pytest.fixture(name="re_sequenced_sample_store")
def fixture_re_sequenced_sample_store(
    store: Store,
    case_id: str,
    family_name: str,
    flowcell_name,
    sample_id: str,
    ticket_number: int,
    helpers,
) -> Store:
    """Populate a store with a Fluffy case, with a sample that has been sequenced on two flow cells"""
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
        application_type="tgs",
        reads=1200000000,
        store=re_sequenced_sample_store,
        ticket=ticket_number,
        sequenced_at=dt.datetime.now(),
    )

    now = dt.datetime.now()
    one_day_ahead_of_now = now + dt.timedelta(days=1)

    helpers.add_flowcell(
        store=re_sequenced_sample_store, flowcell_id="HF57HDRXY", samples=[store_sample], date=now
    )

    helpers.add_flowcell(
        store=re_sequenced_sample_store,
        flowcell_id=flowcell_name,
        samples=[store_sample],
        date=one_day_ahead_of_now,
    )

    helpers.add_relationship(store=re_sequenced_sample_store, case=store_case, sample=store_sample)

    return re_sequenced_sample_store
