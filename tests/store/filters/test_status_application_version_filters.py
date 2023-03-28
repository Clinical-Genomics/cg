from typing import List, Tuple, Iterable
import datetime as dt

from sqlalchemy.orm import Query

from cg.store import Store
from cg.store.filters.status_application_version_filters import (
    filter_application_versions_by_application_id,
    filter_application_versions_by_application,
    filter_application_versions_before_valid_from,
    filter_application_versions_by_version,
    order_application_versions_by_valid_from_desc,
    apply_application_versions_filter,
    ApplicationVersionFilter,
)
from cg.store.models import Application, ApplicationVersion

from tests.store.api.conftest import (
    fixture_applications_store,
)
from tests.store_helpers import StoreHelpers


def test_filter_application_version_by_application_correct_application(
    store_with_different_application_versions: Store,
    helpers: StoreHelpers,
):
    """Test that the application of the filtered application version is the correct one."""
    # GIVEN a store with different applications
    applications: List[Application] = store_with_different_application_versions.get_applications()
    linked_application: Application = applications[0]
    unlinked_application: Application = applications[-1]
    assert unlinked_application != linked_application

    # GIVEN that one application has a linked application version in the store
    app_version_query: Query = store_with_different_application_versions._get_query(
        table=ApplicationVersion
    )
    assert app_version_query.first().application == linked_application

    # WHEN filtering an application version query by the linked application
    filtered_app_version_query: Query = filter_application_versions_by_application(
        application_versions=app_version_query,
        application=linked_application,
    )

    # THEN the filtered query has fewer entries than the unfiltered query
    assert app_version_query.count() > filtered_app_version_query.count()

    # THEN the application of the filtered query entries is equal to the application used to filter
    filtered_applications: List[Application] = [
        application_version.application for application_version in filtered_app_version_query.all()
    ]
    assert all(
        filtered_application == linked_application for filtered_application in filtered_applications
    )


def test_filter_application_version_by_application_wrong_application_returns_empty(
    store_with_different_application_versions: Store,
    helpers: StoreHelpers,
    wgs_application_tag: str,
):
    """Test that the filtering by application returns an empty query if the wrong application is used."""
    # GIVEN a store populated with application versions
    app_version_query: Query = store_with_different_application_versions._get_query(
        table=ApplicationVersion
    )

    # GIVEN an application
    application: Application = helpers.ensure_application(
        store=store_with_different_application_versions,
        tag=wgs_application_tag,
    )
    assert application

    # GIVEN that the application is not linked to any application version in the store
    tags_in_store: List[str] = [
        application_version.application.tag
        for application_version in store_with_different_application_versions.get_application_versions()
    ]
    assert application.tag not in tags_in_store

    # WHEN filtering the application version query by the unlinked application
    filtered_app_version_query: Query = filter_application_versions_by_application(
        application_versions=app_version_query,
        application=application,
    )

    # THEN the filtered query is empty
    assert filtered_app_version_query.count() == 0


def test_filter_application_version_by_application_id_correct_id(
    store_with_different_application_versions: Store,
    helpers: StoreHelpers,
):
    """Test that the correct application version is returned when using a correct application id."""
    # GIVEN a store with application versions
    app_version_query: Query = store_with_different_application_versions._get_query(
        table=ApplicationVersion
    )

    # GIVEN an application in store different in id from at least another application in store
    application: Application = store_with_different_application_versions.get_applications()[0]
    assert application.id != store_with_different_application_versions.get_applications()[1]

    # WHEN the application version query is filtered by the id of the application
    filtered_app_version_query: Query = filter_application_versions_by_application_id(
        application_versions=app_version_query,
        application_id=application.id,
    )

    # THEN the filtered query is shorter than the unfiltered query
    assert app_version_query.count() > filtered_app_version_query.count()

    # THEN the application id of all the filtered query entries is equal to the id used to filter
    application_ids: List[int] = [
        application_version.application_id
        for application_version in filtered_app_version_query.all()
    ]
    assert all(application_id == application.id for application_id in application_ids)


def test_filter_application_version_by_application_id_wrong_id(
    store_with_different_application_versions: Store,
    helpers: StoreHelpers,
    invalid_application_id: int,
):
    """Test that an empty query is returned when using an incorrect application id."""
    # GIVEN a store with application versions
    app_version_query: Query = store_with_different_application_versions._get_query(
        table=ApplicationVersion
    )

    # WHEN filtering with an invalid application id
    filtered_app_version_query: Query = filter_application_versions_by_application_id(
        application_versions=app_version_query,
        application_id=invalid_application_id,
    )

    # THEN the filtered query is empty
    assert filtered_app_version_query.count() == 0


def test_filter_application_version_by_application_id_empty_query(
    store: Store, application_id: int = 1
):
    """Test that filtering an empty query by application id returns an empty query."""
    # GIVEN a store without any application version
    app_version_query: Query = store._get_query(table=ApplicationVersion)
    assert app_version_query.count() == 0

    # WHEN filtering by application id
    filtered_app_version_query: Query = filter_application_versions_by_application_id(
        application_versions=app_version_query,
        application_id=application_id,
    )

    # THEN the function returns an empty query
    assert isinstance(filtered_app_version_query, Query)
    assert filtered_app_version_query.count() == 0


def test_filter_application_versions_before_valid_from_valid_date(
    store_with_different_application_versions: Store,
):
    """Test that filtering by `valid_from` returns a query with older elements than the given date."""
    # GIVEN a store with application versions with different dates
    app_version_query: Query = store_with_different_application_versions._get_query(
        table=ApplicationVersion
    ).order_by(ApplicationVersion.valid_from)
    first_app_version: ApplicationVersion = app_version_query.first()
    third_app_version: ApplicationVersion = app_version_query.offset(2).first()
    assert first_app_version.valid_from < third_app_version.valid_from

    # WHEN filtering the application version query by `valid_from` of the third query
    filtered_app_version_query: Query = filter_application_versions_before_valid_from(
        application_versions=app_version_query,
        valid_from=third_app_version.valid_from,
    )

    # THEN a query with the two first application versions is returned
    assert filtered_app_version_query.count() == 2

    # THEN the date of the newest filtered application version is older than the filter date.
    newest_application_version: ApplicationVersion = filtered_app_version_query.order_by(
        ApplicationVersion.valid_from.desc()
    ).first()
    assert newest_application_version.valid_from < third_app_version.valid_from


def test_filter_application_versions_before_valid_from_future_date(
    store_with_different_application_versions: Store,
    future_date: dt.datetime,
):
    """Test that filtering by `valid_from` with a future date returns the unfiltered query."""
    # GIVEN a store with application versions
    app_version_query: Query = store_with_different_application_versions._get_query(
        table=ApplicationVersion
    )

    # WHEN filtering using a future date
    filtered_app_version_query: Query = filter_application_versions_before_valid_from(
        application_versions=app_version_query,
        valid_from=future_date,
    )

    # THEN the filtered query has the same elements as the unfiltered query
    app_version_pair: Iterable[Tuple[ApplicationVersion, ApplicationVersion]] = zip(
        app_version_query.all(), filtered_app_version_query.all()
    )
    assert all(non_filtered == filtered for non_filtered, filtered in app_version_pair)


def test_filter_application_versions_before_valid_from_old_date(
    store_with_different_application_versions: Store,
    old_timestamp: dt.datetime,
):
    """Test that filtering by `valid_from` with an old date returns an empty query."""
    # GIVEN a store with application versions
    app_version_query: Query = store_with_different_application_versions._get_query(
        table=ApplicationVersion
    )

    # WHEN filtering using a past date
    filtered_app_version_query: Query = filter_application_versions_before_valid_from(
        application_versions=app_version_query,
        valid_from=old_timestamp,
    )

    # THEN the filtered query is empty
    assert filtered_app_version_query.count() == 0


def test_filter_application_version_before_valid_from_empty_query(
    store: Store,
    timestamp_now: dt.datetime,
):
    """Test that filtering an empty query by valid_from returns an empty query."""
    # GIVEN a store without any application version
    app_version_query: Query = store._get_query(table=ApplicationVersion)
    assert app_version_query.count() == 0

    # WHEN filtering by application id
    filtered_app_version_query: Query = filter_application_versions_before_valid_from(
        application_versions=app_version_query,
        valid_from=timestamp_now,
    )

    # THEN the function returns an empty query
    assert isinstance(filtered_app_version_query, Query)
    assert filtered_app_version_query.count() == 0


def test_filter_application_version_by_version_correct_version(
    store_with_different_application_versions: Store,
):
    """Test that filtering by a valid version returns an application version with the correct version."""
    # GIVEN a store with application versions with different versions
    app_version_query: Query = store_with_different_application_versions._get_query(
        table=ApplicationVersion
    ).order_by(ApplicationVersion.version)
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
    # THEN the version of all the filtered query entries is equal to the version used to filter
    versions: List[int] = [
        application_version.version for application_version in filtered_app_version_query.all()
    ]
    assert all(version == version_to_filter for version in versions)


def test_filter_application_version_by_version_invalid_version_returns_empty(
    store_with_different_application_versions: Store,
    invalid_application_version_version: int,
):
    """Test that an empty query is returned if a non-existent version is used to filter."""
    # GIVEN a store with application versions
    app_version_query: Query = store_with_different_application_versions._get_query(
        table=ApplicationVersion,
    )

    # WHEN filtering by version using an invalid version
    filtered_app_version_query: Query = filter_application_versions_by_version(
        application_versions=app_version_query,
        version=invalid_application_version_version,
    )

    # THEN the filtered query is empty
    assert filtered_app_version_query.count() == 0


def test_filter_application_version_by_version_empty_query(store: Store, version: int = 1):
    """Test that filtering an empty query by version returns an empty query."""
    # GIVEN a store without any application version
    app_version_query: Query = store._get_query(table=ApplicationVersion)
    assert app_version_query.count() == 0

    # WHEN filtering by application id
    filtered_app_version_query: Query = filter_application_versions_by_version(
        application_versions=app_version_query,
        version=version,
    )

    # THEN the function returns an empty query
    assert isinstance(filtered_app_version_query, Query)
    assert filtered_app_version_query.count() == 0


def test_order_application_versions_by_valid_from_desc(
    store_with_different_application_versions: Store,
):
    """Test that ordering an application version query returns a query ordered by 'valid_from'."""
    # GIVEN a store with application versions with different dates
    app_version_query: Query = store_with_different_application_versions._get_query(
        table=ApplicationVersion
    )

    # WHEN ordering the query by `valid_from`
    ordered_app_versions: List[ApplicationVersion] = list(
        order_application_versions_by_valid_from_desc(application_versions=app_version_query)
    )
    n_app_versions: int = len(ordered_app_versions)

    # THEN the elements of the ordered query have descending order of valid_from
    assert all(
        ordered_app_versions[i].valid_from > ordered_app_versions[i + 1].valid_from
        for i in range(n_app_versions - 1)
    )


def test_order_application_versions_by_valid_from_desc_empty_query(store: Store):
    """Test that ordering an empty query by valid_from returns an empty query."""
    # GIVEN a store without any application version
    app_version_query: Query = store._get_query(table=ApplicationVersion)
    assert app_version_query.count() == 0

    # WHEN filtering by application id
    ordered_app_version_query: Query = order_application_versions_by_valid_from_desc(
        application_versions=app_version_query
    )

    # THEN the function returns an empty query
    assert isinstance(ordered_app_version_query, Query)
    assert ordered_app_version_query.count() == 0
