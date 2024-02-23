import datetime as dt
from typing import Iterable

from sqlalchemy.orm import Query

from cg.store.filters.status_application_version_filters import (
    filter_application_versions_before_valid_from,
    filter_application_versions_by_application_entry_id,
    filter_application_versions_by_application_version_entry_id,
    order_application_versions_by_valid_from_desc,
)
from cg.store.models import Application, ApplicationVersion
from cg.store.store import Store


def test_filter_application_version_by_application_entry_id_correct_id(
    base_store: Store,
):
    """Test that the correct application version is returned when using a correct application entry id."""
    # GIVEN a store with application versions
    app_version_query: Query = base_store._get_query(table=ApplicationVersion)

    # GIVEN an application in store different in id from at least another application in store
    application: Application = base_store.get_applications()[0]
    assert application.id != base_store.get_applications()[1].id

    # WHEN the application version query is filtered by the id of the application
    filtered_app_version_query: Query = filter_application_versions_by_application_entry_id(
        application_versions=app_version_query,
        application_entry_id=application.id,
    )

    # THEN the filtered query is shorter than the unfiltered query
    assert app_version_query.count() > filtered_app_version_query.count()

    # THEN the application id of all the filtered query entries is equal to the id used to filter
    application_ids: list[int] = [
        application_version.application_id
        for application_version in filtered_app_version_query.all()
    ]
    assert all(application_id == application.id for application_id in application_ids)


def test_filter_application_version_by_application_entry_id_wrong_id(
    base_store: Store,
    invalid_application_id: int,
):
    """Test that an empty query is returned when using an incorrect application id."""
    # GIVEN a store with application versions
    app_version_query: Query = base_store._get_query(table=ApplicationVersion)

    # WHEN filtering with an invalid application id
    filtered_app_version_query: Query = filter_application_versions_by_application_entry_id(
        application_versions=app_version_query,
        application_entry_id=invalid_application_id,
    )

    # THEN the filtered query is empty
    assert filtered_app_version_query.count() == 0


def test_filter_application_version_by_application_entry_id_empty_query(
    store: Store, application_id: int = 1
):
    """Test that filtering an empty query by application entry id returns an empty query."""
    # GIVEN a store without any application version
    app_version_query: Query = store._get_query(table=ApplicationVersion)
    assert app_version_query.count() == 0

    # WHEN filtering by application id
    filtered_app_version_query: Query = filter_application_versions_by_application_entry_id(
        application_versions=app_version_query,
        application_entry_id=application_id,
    )

    # THEN the function returns an empty query
    assert isinstance(filtered_app_version_query, Query)
    assert filtered_app_version_query.count() == 0


def test_filter_application_versions_before_valid_from_valid_date(
    base_store: Store,
):
    """Test that filtering by `valid_from` returns a query with older elements than the given date."""
    # GIVEN a store with application versions with different dates
    app_version_query: Query = base_store._get_query(table=ApplicationVersion).order_by(
        ApplicationVersion.valid_from
    )
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
    base_store: Store,
    future_date: dt.datetime,
):
    """Test that filtering by `valid_from` with a future date returns the unfiltered query."""
    # GIVEN a store with application versions
    app_version_query: Query = base_store._get_query(table=ApplicationVersion)

    # WHEN filtering using a future date
    filtered_app_version_query: Query = filter_application_versions_before_valid_from(
        application_versions=app_version_query,
        valid_from=future_date,
    )

    # THEN the filtered query has the same elements as the unfiltered query
    app_version_pair: Iterable[tuple[ApplicationVersion, ApplicationVersion]] = zip(
        app_version_query.all(), filtered_app_version_query.all()
    )
    assert all(non_filtered == filtered for non_filtered, filtered in app_version_pair)


def test_filter_application_versions_before_valid_from_old_date(
    base_store: Store,
    old_timestamp: dt.datetime,
):
    """Test that filtering by `valid_from` with an old date returns an empty query."""
    # GIVEN a store with application versions
    app_version_query: Query = base_store._get_query(table=ApplicationVersion)

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


def test_order_application_versions_by_valid_from_desc(
    base_store: Store,
):
    """Test that ordering an application version query returns a query ordered by 'valid_from'."""
    # GIVEN a store with application versions with different dates
    app_version_query: Query = base_store._get_query(table=ApplicationVersion)

    # WHEN ordering the query by `valid_from`
    ordered_app_versions: list[ApplicationVersion] = list(
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


def test_filter_application_versions_by_application_version_entry_id_no_match(
    store_with_different_application_versions: Store,
):
    """Test that no application versions are returned when there is no matching application version entry id."""
    # GIVEN a store containing multiple application versions
    application_versions_query: Query = store_with_different_application_versions._get_query(
        table=ApplicationVersion
    )
    non_existent_application_version_entry_id = "non_existent_application_version_entry_id"

    # WHEN filtering application versions by a non-matching application version entry id
    filtered_application_versions: Query = (
        filter_application_versions_by_application_version_entry_id(
            application_versions=application_versions_query,
            application_version_entry_id=non_existent_application_version_entry_id,
        )
    )

    # THEN the query should return no application versions
    assert filtered_application_versions.count() == 0


def test_filter_application_versions_by_application_version_entry_id_match(
    store_with_different_application_versions: Store,
):
    """Test that application versions with matching application version entry id are returned."""
    # GIVEN a store containing multiple application versions
    application_versions_query: Query = store_with_different_application_versions._get_query(
        table=ApplicationVersion
    )
    existing_application_version_entry_id = application_versions_query.first().id

    # WHEN filtering application versions by a matching application version entry id
    filtered_application_versions: Query = (
        filter_application_versions_by_application_version_entry_id(
            application_versions=application_versions_query,
            application_version_entry_id=existing_application_version_entry_id,
        )
    )

    # THEN the query should return the application version with the matching entry id
    assert filtered_application_versions.count() == 1
    assert filtered_application_versions.first().id == existing_application_version_entry_id
