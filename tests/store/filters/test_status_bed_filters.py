from sqlalchemy.orm import Query

from cg.store import Store
from cg.store.filters.status_bed_filters import get_not_archived_beds, order_beds_by_name
from cg.store.models import Bed


def test_get_beds_by_name(base_store: Store, bed_name: str):
    """Test return bed by name."""
    # GIVEN a store containing bed

    # WHEN retrieving a beds by name
    beds: Query = get_not_archived_beds(beds=base_store._get_query(table=Bed))

    # ASSERT that the beds is a query
    assert isinstance(beds, Query)

    # THEN beds should be returned
    assert beds

    # THEN the bed attribute name should match the original
    assert beds[0].name == bed_name


def test_get_not_archived_beds(base_store: Store):
    """Test return bed not archived."""
    # GIVEN a store containing bed

    # WHEN retrieving a beds not archived
    beds: Query = get_not_archived_beds(beds=base_store._get_query(table=Bed))

    # ASSERT that the beds is a query
    assert isinstance(beds, Query)

    # THEN beds should be returned
    assert beds

    # THEN the bed attribute is_archived should be False
    assert beds[0].is_archived is False


def test_order_beds_by_name(base_store: Store, bed_name: str):
    """Test return bed ordered by name."""
    # GIVEN a store containing bed

    # WHEN retrieving a beds
    beds: Query = order_beds_by_name(beds=base_store._get_query(table=Bed))

    # ASSERT that the beds is a query
    assert isinstance(beds, Query)

    # THEN a bed should be returned
    assert beds

    # THEN the bed attribute name should match the original
    assert beds[0].name == bed_name
