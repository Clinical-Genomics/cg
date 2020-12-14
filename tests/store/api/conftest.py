from typing import Iterable
from cg.store import Store
from cg.store.api.models import ApplicationVersionSchema

from tests.store_helpers import StoreHelpers

import pytest

from cg.store.api.import_func import parse_applications


@pytest.fixture(name="applications_store")
def fixture_applications_store(
    store: Store, application_versions_file: str, helpers: StoreHelpers
) -> Store:
    """Return a store populated with applications from excel file"""
    versions: Iterable[ApplicationVersionSchema] = parse_applications(
        excel_path=application_versions_file
    )

    for version in versions:
        helpers.ensure_application(store=store, tag=version.app_tag)

    return store
