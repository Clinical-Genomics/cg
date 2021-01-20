from typing import Iterable, List

import pytest

from cg.store import Store, models
from cg.store.api.import_func import (
    parse_application_versions,
    parse_applications,
    versions_are_same,
)
from cg.store.api.models import ApplicationSchema, ApplicationVersionSchema
from tests.store_helpers import StoreHelpers


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
