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
    store_with_two_applications_one_with_application_version: Store,
    helpers: StoreHelpers,
):
    """Test that the application of the filtered application version is the correct one."""
    # GIVEN a store with two applications
    app_query: Query = store_with_two_applications_one_with_application_version._get_query(
        table=Application
    )
    assert app_query.count() == 2

    # GIVEN that the applications are different
    unlinked_app: Application = app_query.first()
    linked_app: Application = app_query.order_by(desc(Application.id)).first()
    assert str(unlinked_app) != str(linked_app)

    # GIVEN that the store has one application version of one application
    app_version_query: Query = store_with_two_applications_one_with_application_version._get_query(
        table=ApplicationVersion
    )
    assert app_version_query.count() == 1
    assert str(app_version_query.first().application) == str(linked_app)

    # WHEN filtering an application version query by the linked application
    application_versions: Query = filter_application_version_by_application(
        application_versions=app_version_query,
        application=linked_app,
    )

    # THEN the application of the application version in the filter query is the same as the input application
    assert str(application_versions.first().application) == str(linked_app)


def test_filter_application_version_by_application_no_application_returns_none(
    store_with_two_applications_one_with_application_version: Store,
    helpers: StoreHelpers,
):
    """Test that the filtering by application returns None if the application is not present"""
    # GIVEN a store with two applications
    app_query: Query = store_with_two_applications_one_with_application_version._get_query(
        table=Application
    )
    assert app_query.count() == 2

    # GIVEN that the applications are different
    unlinked_app: Application = app_query.first()
    linked_app: Application = app_query.order_by(desc(Application.id)).first()
    assert str(unlinked_app) != str(linked_app)

    # GIVEN that the store has one application version of one application
    app_version_query: Query = store_with_two_applications_one_with_application_version._get_query(
        table=ApplicationVersion
    )
    assert app_version_query.count() == 1
    assert str(app_version_query.first().application) == str(linked_app)

    # WHEN filtering the application version query by the unlinked application
    application_versions: Query = filter_application_version_by_application(
        application_versions=app_version_query,
        application=unlinked_app,
    )

    # THEN the query is empty
    assert application_versions.count() == 0


def test_filter_application_version_by_application_id(
    store: Store,
    helpers: StoreHelpers,
):
    """."""
    # GIVEN

    # WHEN

    # THEN


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
