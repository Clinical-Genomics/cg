from typing import List

from sqlalchemy import desc
from sqlalchemy.orm import Query

from cg.store import Store
from cg.store.filters.status_application_version_filters import (
    filter_application_versions_by_application_id,
    filter_application_versions_by_application,
    filter_application_versions_before_date,
    filter_application_versions_by_version,
    order_application_versions_by_desc_date,
)

from cg.store.models import Application, ApplicationVersion

from tests.store.api.conftest import (
    fixture_applications_store,
)
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
    # GIVEN a store with an application version
    app_version_query: Query = store_with_applications_with_application_versions._get_query(
        table=ApplicationVersion
    )

    # WHEN filtering with an invalid application id
    filtered_app_version_query: Query = filter_application_versions_by_application_id(
        application_versions=app_version_query,
        application_id=invalid_application_id,
    )

    # THEN the filtered query is empty
    assert filtered_app_version_query.count() == 0


def test_filter_application_versions_before_date(store_with_different_application_versions: Store):
    """Test that filtering by date returns a query with older elements than the given date."""
    # GIVEN a store with application versions with different dates
    app_version_query: Query = store_with_different_application_versions._get_query(
        table=ApplicationVersion
    ).order_by(ApplicationVersion.valid_from)
    first_app_version: ApplicationVersion = app_version_query.first()
    third_app_version: ApplicationVersion = app_version_query.offset(2).first()
    assert first_app_version.valid_from < third_app_version.valid_from

    # WHEN filtering the application version query by the date of the third query
    filtered_app_version_query: Query = filter_application_versions_before_date(
        application_versions=app_version_query,
        date=third_app_version.valid_from,
    )

    # THEN a query with the two first application versions are returned
    assert filtered_app_version_query.count() == 2
    # THEN the date of the newest query is older than the filter date.
    assert (
        filtered_app_version_query.order_by(desc(ApplicationVersion.valid_from)).first().valid_from
        < third_app_version.valid_from
    )


def test_filter_application_version_by_version_correct_version(
    store_with_one_application_and_two_versions: Store,
):
    """Test that filtering by a valid version returns an application version with the correct version."""
    # GIVEN a store with two application versions with different versions
    app_version_query: Query = store_with_one_application_and_two_versions._get_query(
        table=ApplicationVersion
    )
    version_to_filter: int = app_version_query.first().version
    version_to_exclude: int = app_version_query.offset(1).first().version
    assert version_to_filter != version_to_exclude

    # WHEN filtering the application version query using the valid version
    filtered_app_version_query: Query = filter_application_versions_by_version(
        application_versions=app_version_query,
        version=version_to_filter,
    )

    # THEN the filtered query has fewer elements than the unfiltered query
    assert filtered_app_version_query.count() < app_version_query.count()
    # THEN the version of the application version is the same as inputted to the filter
    assert filtered_app_version_query.first().version == version_to_filter


def test_filter_application_version_by_version_invalid_version_returns_empty(
    store_with_one_application_and_two_versions: Store,
    invalid_application_version_version: int,
):
    """."""
    # GIVEN a store with application versions and an invalid version
    app_version_query: Query = store_with_one_application_and_two_versions._get_query(
        table=ApplicationVersion,
    )

    # WHEN filtering by version using the invalid version
    filtered_app_version_query: Query = filter_application_versions_by_version(
        application_versions=app_version_query,
        version=invalid_application_version_version,
    )

    # THEN the filtered query is empty
    assert filtered_app_version_query.count() == 0


def test_order_application_versions_by_desc_date(store_with_different_application_versions: Store):
    """."""
    # GIVEN a store with application versions with different dates
    app_version_query: Query = store_with_different_application_versions._get_query(
        table=ApplicationVersion
    )

    # WHEN ordering the query by date
    ordered_app_versions: List[ApplicationVersion] = list(
        order_application_versions_by_desc_date(application_versions=app_version_query)
    )
    n_app_versions: int = len(ordered_app_versions)

    # THEN the elements of the ordered query have descending order of valid_from
    assert all(
        ordered_app_versions[i].valid_from > ordered_app_versions[i + 1].valid_from
        for i in range(n_app_versions - 1)
    )
