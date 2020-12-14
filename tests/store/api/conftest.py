from typing import Iterable
from cg.store import Store
from cg.store.api.models import ApplicationVersionSchema

from tests.store_helpers import StoreHelpers

import pytest

from cg.store.api.import_func import parse_application_versions


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
