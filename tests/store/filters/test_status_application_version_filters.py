from typing import List

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

from tests.store_helpers import StoreHelpers


def test_filter_application_version_by_application_correct_application(
    store_with_applications_with_application_versions: Store,
    helpers: StoreHelpers,
):
    """Test that the application of the filtered application version is the correct one."""
    # GIVEN a store with different applications
    applications: List[
        Application
    ] = store_with_applications_with_application_versions.get_applications()
    linked_app: Application = applications[0]
    unlinked_app: Application = applications[-1]
    assert str(unlinked_app) != str(linked_app)

    # GIVEN that one application has a linked application version in the store
    app_version_query: Query = store_with_applications_with_application_versions._get_query(
        table=ApplicationVersion
    )
    assert str(app_version_query.first().application) == str(linked_app)

    # WHEN filtering an application version query by the linked application
    filtered_app_version_query: Query = filter_application_version_by_application(
        application_versions=app_version_query,
        application=linked_app,
    )

    # THEN the filtered query has fewer entries than the unfiltered query
    assert app_version_query.count() > filtered_app_version_query.count()
    # THEN the application of the application version in the filter query is the linked application
    assert str(filtered_app_version_query.first().application) == str(linked_app)


def test_filter_application_version_by_application_no_application_returns_empty(
    store_with_applications_with_application_versions: Store,
    helpers: StoreHelpers,
    wgs_application_tag: str,
):
    """Test that the filtering by application returns an empty query if the application is not present."""
    # GIVEN a store with different applications
    local_store: Store = store_with_applications_with_application_versions
    applications: List[Application] = local_store.get_applications()
    linked_app: Application = applications[0]
    unlinked_app: Application = local_store.get_application_by_tag(wgs_application_tag)
    assert str(unlinked_app) != str(linked_app)

    # GIVEN that one application has a linked application version in the store
    app_version_query: Query = store_with_applications_with_application_versions._get_query(
        table=ApplicationVersion
    )
    assert str(app_version_query.first().application) == str(linked_app)

    # WHEN filtering the application version query by the unlinked application
    filtered_app_version_query: Query = filter_application_version_by_application(
        application_versions=app_version_query,
        application=unlinked_app,
    )

    # THEN the query is empty
    assert filtered_app_version_query.count() == 0


def test_filter_application_version_by_application_id_correct_id(
    store_with_applications_with_application_versions: Store,
    helpers: StoreHelpers,
):
    """."""
    # GIVEN a store with application versions and their applications
    local_store: Store = store_with_applications_with_application_versions
    app_version_query: Query = local_store._get_query(table=ApplicationVersion)

    # GIVEN two applications with different ids
    app_filter: Application = local_store.get_applications()[0]
    app_not_filter: Application = local_store.get_applications()[-1]
    assert app_filter.id != app_not_filter.id

    # WHEN the application version query is filtered by the id on an application
    filtered_app_version_query: Query = filter_application_version_by_application_id(
        application_versions=app_version_query,
        application_id=app_filter.id,
    )

    # THEN the filtered query is shorter than the unfiltered query
    assert app_version_query.count() > filtered_app_version_query.count()

    # THEN the application id of the filter input is the same as the ones in the filtered query
    assert filtered_app_version_query.first().application_id == app_filter.id


def test_filter_application_version_newer_than_date():
    """."""
    # GIVEN

    # WHEN

    # THEN


def test_filter_application_version_by_version():
    """."""
    # GIVEN

    # WHEN

    # THEN
