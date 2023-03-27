from cg.store.filters.status_application_filters import (
    filter_applications_by_entry_id,
    filter_applications_by_prep_category,
    filter_applications_by_tag,
    filter_applications_is_archived,
    filter_applications_is_external,
    filter_applications_is_not_external,
    filter_applications_is_not_archived,
)

from cg.store import Store
from cg.store.models import Application
from sqlalchemy.orm import Query
from tests.store.conftest import StoreConftestFixture


def test_filter_get_application_by_tag(
    store_with_an_application_with_and_without_attributes: Store,
    tag=StoreConftestFixture.TAG_APPLICATION_WITH_ATTRIBUTES.value,
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


def test_filter_get_applications_by_prep_category(
    store_with_an_application_with_and_without_attributes: Store,
    prep_category=StoreConftestFixture.PREP_CATEGORY_APPLICATION_WITH_ATTRIBUTES.value,
) -> None:
    """Test to get application by prep category."""
    #  GIVEN a store with two applications of which one is of a prep category

    # WHEN getting an application by prep category
    application: Query = filter_applications_by_prep_category(
        applications=store_with_an_application_with_and_without_attributes._get_query(
            table=Application
        ),
        prep_category=prep_category,
    )

    # ASSERT that application is a query
    assert isinstance(application, Query)

    # THEN assert the application was found
    assert (
        application.all()
        and len(application.all()) == 1
        and application.all()[0].prep_category == prep_category
    )


def test_filter_get_applications_is_archived(
    store_with_an_application_with_and_without_attributes: Store,
) -> None:
    """Test to get application by is_archived."""
    # GIVEN a store with two applications of which one is archived

    # WHEN getting an application by is_archived
    application: Query = filter_applications_is_archived(
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
        and application.all()[0].is_archived is True
    )


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


def test_filter_get_applications_by_entry_id(
    store_with_an_application_with_and_without_attributes: Store,
    entry_id: int = 1,
) -> None:
    """Test to get application by id."""
    # GIVEN a database with an application two applications

    # WHEN getting an application by id
    application: Query = filter_applications_by_entry_id(
        applications=store_with_an_application_with_and_without_attributes._get_query(
            table=Application
        ),
        entry_id=entry_id,
    )

    # ASSERT that applications is a query
    assert isinstance(application, Query)

    # THEN assert the application was found
    assert application.all() and len(application.all()) == 1 and application.all()[0].id == entry_id
