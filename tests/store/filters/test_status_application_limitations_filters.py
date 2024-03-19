from sqlalchemy.orm import Query

from cg.constants import Workflow
from cg.store.filters.status_application_limitations_filters import (
    filter_application_limitations_by_tag,
    filter_application_limitations_by_workflow,
)
from cg.store.store import Store
from tests.store.conftest import StoreConstants


def test_filter_application_limitations_by_tag(
    store_with_application_limitations: Store,
    tag=StoreConstants.TAG_APPLICATION_WITH_ATTRIBUTES.value,
) -> None:
    """Test to get application limitations by tag."""

    # GIVEN a store with application limitations

    # WHEN getting an application limitations by tag
    application_limitations: Query = filter_application_limitations_by_tag(
        application_limitations=store_with_application_limitations._get_join_application_limitations_query(),
        tag=tag,
    )

    # ASSERT that application limitations is a query
    assert isinstance(application_limitations, Query)

    # THEN assert that the application limitations was found
    assert (
        application_limitations.all()
        and len(application_limitations.all()) == 1
        and application_limitations.all()[0].application.tag == tag
    )


def test_filter_application_limitations_by_workflow(
    store_with_application_limitations: Store,
    workflow=Workflow.BALSAMIC,
) -> None:
    """Test to get application limitations by workflow."""

    # GIVEN a store with application limitations

    # WHEN getting an application limitations by workflow
    application_limitations: Query = filter_application_limitations_by_workflow(
        application_limitations=store_with_application_limitations._get_join_application_limitations_query(),
        workflow=workflow,
    )

    # ASSERT that application limitations is a query
    assert isinstance(application_limitations, Query)

    # THEN assert the application limitations was found
    assert (
        application_limitations.all()
        and len(application_limitations.all()) == 1
        and application_limitations.all()[0].workflow == workflow
    )
