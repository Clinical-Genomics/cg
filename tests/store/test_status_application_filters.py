from cg.store.status_application_filters import (
    get_application_by_id,
    get_application_by_prep_category,
    get_application_by_tag,
    get_application_by_version,
    get_application_is_archived,
    get_application_is_external,
    get_application_is_not_external,
    get_application_valid_from,
)
from cg.store.models import Application
from cg.store import Store
from tests.store_helpers import StoreHelpers
from typing import List
from sqlalchemy.orm import Query
from datetime import datetime, timedelta


def test_filter_get_application_by_tag(
    store: Store, helpers: StoreHelpers, tags: List[str] = ["WGTPCFC030", "WGTPCFC031"]
) -> None:
    """Test to get application by tag."""
    # GIVEN a database with an application
    helpers.ensure_application(store=store, tag=tags[0])
    helpers.ensure_application(store=store, tag=tags[1])

    # ASSERT that there are two applications in the database
    assert store.applications().count() == 2

    # WHEN getting an application by tag
    applications: Query = store._get_application_query()

    # WHEN getting an application by tag
    application: List[Query] = list(get_application_by_tag(applications=applications, tag=tags[0]))

    # THEN assert the application was found
    assert application and len(application) == 1


def test_filter_get_application_by_prep_category(
    store: Store, helpers: StoreHelpers, prep_categories: List[str] = ["wgs", "wes"]
) -> None:
    """Test to get application by prep category."""
    # GIVEN a database with an application
    helpers.ensure_application(store=store, prep_category=prep_categories[0], tag="WGTPCFC031")
    helpers.ensure_application(store=store, prep_category=prep_categories[1], tag="WGTPCFC030")

    # ASSERT that there are two applications in the database
    assert store.applications().count() == 2

    # WHEN getting an application by prep category
    applications: Query = store._get_application_query()

    # WHEN getting an application by prep category
    application: List[Query] = list(
        get_application_by_prep_category(
            applications=applications, prep_category=prep_categories[0]
        )
    )

    # THEN assert the application was found
    assert application and len(application) == 1


def test_filter_get_application_is_archived(
    store: Store, helpers: StoreHelpers, tag: List[str] = ["WGTPCFC031", "WGTPCFC030"]
) -> None:
    """Test to get application by is_archived."""
    # GIVEN a database with an application
    helpers.ensure_application(store=store, is_archived=False, tag=tag[0])
    helpers.ensure_application(store=store, is_archived=True, tag=tag[1])

    # ASSERT that there is one application in the database
    assert store.applications().count() == 2

    # WHEN getting an application by is_archived
    applications: Query = store._get_application_query()

    # WHEN getting an application by is_archived
    application: List[Query] = list(get_application_is_archived(applications=applications))

    # THEN assert the application was found
    assert application and len(application) == 1


def test_filter_get_application_is_external(
    store: Store, helpers: StoreHelpers, tag: List[str] = ["WGTPCFC031", "WGTPCFC030"]
) -> None:
    """Test to get application by is_external."""
    # GIVEN a database with an application
    helpers.ensure_application(store=store, is_external=False, tag=tag[0])
    helpers.ensure_application(store=store, is_external=True, tag=tag[1])

    # ASSERT that there is one application in the database
    assert store.applications().count() == 2

    # WHEN getting an application by is_external
    applications: Query = store._get_application_query()

    # WHEN getting an application by is_external
    application: List[Query] = list(get_application_is_external(applications=applications))

    # THEN assert the application was found
    assert application and len(application) == 1


def test_filter_get_application_is_not_external(
    store: Store, helpers: StoreHelpers, tag: List[str] = ["WGTPCFC031", "WGTPCFC030"]
) -> None:
    """Test to get application by is_external."""
    # GIVEN a database with an application
    helpers.ensure_application(store=store, is_external=False, tag=tag[0])
    helpers.ensure_application(store=store, is_external=True, tag=tag[1])

    # ASSERT that there is one application in the database
    assert store.applications().count() == 2

    # WHEN getting an application by is_external
    applications: Query = store._get_application_query()

    # WHEN getting an application by is_external
    application: List[Query] = list(get_application_is_not_external(applications=applications))

    # THEN assert the application was found
    assert application and len(application) == 1


def test_filter_get_application_by_id(
    store: Store,
    helpers: StoreHelpers,
    tag: List[str] = ["WGTPCFC031", "WGTPCFC030"],
    application_id: int = 1,
) -> None:
    """Test to get application by id."""
    # GIVEN a database with an application
    helpers.ensure_application(store=store, tag=tag[0])
    helpers.ensure_application(store=store, tag=tag[1])

    # ASSERT that there are two applications in the database
    assert store.applications().count() == 2

    # WHEN getting an application by id
    applications: Query = store._get_application_query()

    # WHEN getting an application by id
    application: List[Query] = list(
        get_application_by_id(applications=applications, application_id=application_id)
    )

    # THEN assert the application was found
    assert application and len(application) == 1
