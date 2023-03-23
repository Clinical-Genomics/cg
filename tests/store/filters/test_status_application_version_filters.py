from typing import List

from cg.store.filters.status_application_version_filters import (
    filter_application_versions_by_application_id,
    filter_application_versions_by_application,
    filter_application_versions_before_date,
    filter_application_versions_by_version,
)

from cg.store import Store
from cg.store.models import Application, ApplicationVersion
from sqlalchemy import desc
from sqlalchemy.orm import Query
from tests.store.api.conftest import fixture_applications_store, fixture_invalid_application_id
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
    linked_application: Application = applications[0]
    unlinked_application: Application = applications[-1]
    assert str(unlinked_application) != str(linked_application)

    # GIVEN that one application has a linked application version in the store
    app_version_query: Query = store_with_applications_with_application_versions._get_query(
        table=ApplicationVersion
    )
    assert str(app_version_query.first().application) == str(linked_application)

    # WHEN filtering an application version query by the linked application
    filtered_app_version_query: Query = filter_application_versions_by_application(
        application_versions=app_version_query,
        application=linked_application,
    )

    # THEN the filtered query has fewer entries than the unfiltered query
    assert app_version_query.count() > filtered_app_version_query.count()
    # THEN the application of the application version in the filter query is the linked application
    assert str(filtered_app_version_query.first().application) == str(linked_application)


def test_filter_application_version_by_application_wrong_application_returns_empty(
    store_with_applications_with_application_versions: Store,
    helpers: StoreHelpers,
    wgs_application_tag: str,
):
    """Test that the filtering by application returns an empty query if the wrong application is used."""
    # GIVEN a store with different applications
    local_store: Store = store_with_applications_with_application_versions
    applications: List[Application] = local_store.get_applications()
    linked_application: Application = applications[0]
    unlinked_application: Application = local_store.get_application_by_tag(wgs_application_tag)
    assert str(unlinked_application) != str(linked_application)

    # GIVEN that one application has a linked application version in the store
    app_version_query: Query = local_store._get_query(table=ApplicationVersion)
    assert str(app_version_query.first().application) == str(linked_application)

    # WHEN filtering the application version query by the unlinked application
    filtered_app_version_query: Query = filter_application_versions_by_application(
        application_versions=app_version_query,
        application=unlinked_application,
    )

    # THEN the query is empty
    assert filtered_app_version_query.count() == 0


def test_filter_application_version_by_application_empty_query_returns_none(
    applications_store: Store, helpers: StoreHelpers
):
    """Test that filtering an empty query returns an empty query."""
    # GIVEN a store with applications but without application versions
    applications: List[Application] = applications_store.get_applications()
    assert applications

    app_version_query: Query = applications_store._get_query(table=ApplicationVersion)
    assert app_version_query.count() == 0

    # WHEN trying to filter by application
    filtered_app_version_query: Query = filter_application_versions_by_application(
        application_versions=app_version_query,
        application=applications[0],
    )

    # THEN the filtered query is empty
    assert filtered_app_version_query.count() == 0


def test_filter_application_version_by_application_id_correct_id(
    store_with_applications_with_application_versions: Store,
    helpers: StoreHelpers,
):
    """Test that the correct application version is returned when using a correct application id."""
    # GIVEN a store with application versions and their applications
    local_store: Store = store_with_applications_with_application_versions
    app_version_query: Query = local_store._get_query(table=ApplicationVersion)

    # GIVEN two applications with different ids
    application: Application = local_store.get_applications()[0]

    # WHEN the application version query is filtered by the id on an application
    filtered_app_version_query: Query = filter_application_versions_by_application_id(
        application_versions=app_version_query,
        application_id=application.id,
    )

    # THEN the filtered query is shorter than the unfiltered query
    assert app_version_query.count() > filtered_app_version_query.count()

    # THEN the application id of the filter input is the same as the ones in the filtered query
    assert filtered_app_version_query.first().application_id == application.id


def test_filter_application_version_by_application_id_wrong_id(
    store_with_applications_with_application_versions: Store,
    helpers: StoreHelpers,
    invalid_application_id: int,
):
    """Test that an empty query is returned when using an incorrect application id."""
    # GIVEN
    app_version_query: Query = store_with_applications_with_application_versions._get_query(
        table=ApplicationVersion
    )

    # WHEN
    filtered_app_version_query: Query = filter_application_versions_by_application_id(
        application_versions=app_version_query,
        application_id=invalid_application_id,
    )

    # THEN
    assert filtered_app_version_query.count() == 0


def test_filter_application_versions_before_date():
    """."""
    # GIVEN

    # WHEN

    # THEN


def test_filter_application_version_by_version():
    """."""
    # GIVEN

    # WHEN

    # THEN
