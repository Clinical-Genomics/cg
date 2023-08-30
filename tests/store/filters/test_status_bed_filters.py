from sqlalchemy.orm import Query

from cg.store import Store
from cg.store.filters.status_bed_filters import (
    get_not_archived_beds,
    order_beds_by_name,
    get_bed_by_entry_id,
    get_bed_by_name,
)
from cg.store.models import Bed


def test_get_bed_by_entry_id(base_store: Store, entry_id: int = 1):
    """Test return panel bed by entry id."""
    # GIVEN a store containing bed

    # WHEN retrieving a bed by id
    bed: Bed = get_bed_by_entry_id(
        beds=base_store._get_query(table=Bed), bed_entry_id=entry_id
    ).first()

    # THEN panel bed should be returned
    assert bed

    # THEN the filename should match the original
    assert bed.id == entry_id


def test_get_bed_by_entry_id_no_id(base_store: Store):
    """Test return panel bed by entry id when invalid id."""
    # GIVEN a store containing bed

    # WHEN retrieving a bed by an invalid id
    bed: Bed = get_bed_by_entry_id(beds=base_store._get_query(table=Bed), bed_entry_id=999).first()

    # THEN bed should not be returned
    assert not bed


def test_get_bed_by_name(base_store: Store, bed_name: str):
    """Test return bed by name."""
    # GIVEN a store containing bed

    # WHEN retrieving a bed by name
    bed: Bed = get_bed_by_name(beds=base_store._get_query(table=Bed), bed_name=bed_name).first()

    # THEN panel bed should be returned
    assert bed

    # THEN the name should match the original
    assert bed.name == bed_name


def test_get_bed_by_name_no_name(base_store: Store):
    """Test return bed by name when no valid name is provided."""
    # GIVEN a store containing bed

    # WHEN retrieving a bed by name
    bed: Bed = get_bed_by_name(beds=base_store._get_query(table=Bed), bed_name="not_a_name").first()

    # THEN panel bed should not be returned
    assert not bed


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
