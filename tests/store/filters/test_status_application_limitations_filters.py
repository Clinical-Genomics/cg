from sqlalchemy.orm import Query

from cg.constants import Pipeline
from cg.store import Store
from cg.store.filters.status_application_limitations_filters import (
    filter_application_limitations_by_pipeline,
    filter_application_limitations_by_tag,
)
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


def test_filter_application_limitations_by_pipeline(
    store_with_application_limitations: Store,
    pipeline=Pipeline.BALSAMIC,
) -> None:
    """Test to get application limitations by pipeline."""

    # GIVEN a store with application limitations

    # WHEN getting an application limitations by pipeline
    application_limitations: Query = filter_application_limitations_by_pipeline(
        application_limitations=store_with_application_limitations._get_join_application_limitations_query(),
        pipeline=pipeline,
    )

    # ASSERT that application limitations is a query
    assert isinstance(application_limitations, Query)

    # THEN assert the application limitations was found
    assert (
        application_limitations.all()
        and len(application_limitations.all()) == 1
        and application_limitations.all()[0].pipeline == pipeline
    )
