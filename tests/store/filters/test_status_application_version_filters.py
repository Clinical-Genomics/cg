from cg.store.filters.status_application_version_filters import (
    filter_application_version_by_application_id,
    filter_application_version_by_application,
    filter_application_version_newer_than_date,
    filter_application_version_by_version,
)

from cg.store import Store
from cg.store.models import Application, ApplicationVersion
from sqlalchemy import desc
from sqlalchemy.orm import Query

from tests.cli.conftest import fixture_application_tag
from tests.store_helpers import StoreHelpers


def test_filter_application_version_by_application_correct_application(
    store: Store, helpers: StoreHelpers, application_tag: str
):
    """Test that the application of the filtered application version is the"""
    # GIVEN an application
    application: Application = helpers.ensure_application(store=store, tag=application_tag)

    # GIVEN an application version with the previous application in the store
    helpers.ensure_application_version(store=store, application=application)

    # WHEN filtering an application version query by application
    application_versions: Query = filter_application_version_by_application(
        application_versions=store._get_query(table=ApplicationVersion),
        application=application,
    )

    # THEN the application of the application version in the filter query is the same as the input application
    assert application_versions.first().application == application


def test_filter_application_version_by_application_no_application_returns_none(
    store: Store,
    helpers: StoreHelpers,
    application_tag: str,
    wgs_application_tag: str,
):
    """Test that the filtering by application returns None if the application is not present"""
    # GIVEN an application version of an application
    application: Application = helpers.ensure_application(
        store=store,
        tag=application_tag,
    )
    helpers.ensure_application_version(
        store=store,
        application=application,
    )

    # GIVEN an application not linked to the application version
    unlinked_application: Application = helpers.ensure_application(
        store=store,
        tag=wgs_application_tag,
    )

    # WHEN filtering the application version query by the unlinked application
    query: Query = filter_application_version_by_application(
        application_versions=store._get_query(table=ApplicationVersion),
        application=unlinked_application,
    )

    # THEN the query is empty
    assert query.count() == 0


def test_filter_application_version_by_application_id(store: Store, helpers: StoreHelpers):
    pass


def test_filter_application_version_newer_than_date():
    pass


def test_filter_application_version_by_version():
    pass
