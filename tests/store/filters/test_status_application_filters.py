from cg.store.filters.status_application_filters import (
    filter_applications_by_tag,
    filter_applications_is_external,
    filter_applications_is_not_external,
    filter_applications_is_not_archived,
)

from cg.store import Store
from cg.store.models import Application
from sqlalchemy.orm import Query
from tests.store.conftest import StoreConstants


def test_filter_get_application_by_tag(
    store_with_an_application_with_and_without_attributes: Store,
    tag=StoreConstants.TAG_APPLICATION_WITH_ATTRIBUTES.value,
) -> None:
    """Test to get application by tag."""
    # GIVEN a store with two applications of which one has a tag

    # WHEN getting an application by tag
    application: Query = filter_applications_by_tag(
        applications=store_with_an_application_with_and_without_attributes._get_query(
            table=Application
        ),
        tag=tag,
    )

    # ASSERT that application is a query
    assert isinstance(application, Query)

    # THEN assert the application was found
    assert application.all() and len(application.all()) == 1 and application.all()[0].tag == tag


def test_filter_application_is_not_archived(
    store_with_an_application_with_and_without_attributes: Store,
) -> None:
    """Test to get application when no archived."""
    # GIVEN a store with two applications of which one is archived

    # WHEN getting an application that is not archived
    application: Query = filter_applications_is_not_archived(
        applications=store_with_an_application_with_and_without_attributes._get_query(
            table=Application
        )
    )

    # ASSERT that application is a query
    assert isinstance(application, Query)

    # THEN assert the application was found
    assert (
        application.all()
        and len(application.all()) == 1
        and application.all()[0].is_archived is False
    )


def test_filter_get_applications_is_external(
    store_with_an_application_with_and_without_attributes: Store,
) -> None:
    """Test to get application by is_external."""
    # GIVEN a store with two applications of which one is external

    # WHEN getting an application by is_external
    application: Query = filter_applications_is_external(
        applications=store_with_an_application_with_and_without_attributes._get_query(
            table=Application
        )
    )

    # ASSERT that application is a query
    assert isinstance(application, Query)

    # THEN assert the application was found
    assert (
        application.all()
        and len(application.all()) == 1
        and application.all()[0].is_external is True
    )


def test_filter_get_applications_is_not_external(
    store_with_an_application_with_and_without_attributes: Store,
) -> None:
    """Test to get application by is_external."""
    # GIVEN a store with two applications of which one is external

    # WHEN getting an application by is_external
    application: Query = filter_applications_is_not_external(
        applications=store_with_an_application_with_and_without_attributes._get_query(
            table=Application
        )
    )

    # ASSERT that application is a query
    assert isinstance(application, Query)

    # THEN assert the application was found
    assert (
        application.all()
        and len(application.all()) == 1
        and application.all()[0].is_external is False
    )
