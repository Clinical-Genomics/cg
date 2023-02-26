from typing import List

from cg.store import Store
from cg.store.models import Bed
from cg.store.status_bed_filters import get_not_archived_beds, order_beds_by_name


def test_get_not_archived_beds(base_store: Store):
    """Test return bed not archived."""
    # GIVEN a store containing bed
    # WHEN retrieving a beds not archived
    beds: List[Bed] = get_not_archived_beds(beds=base_store._get_bed_query())

    # THEN a bed should be returned
    assert beds

    # THEN the bed attribute is_archived should be False
    assert beds[0].is_archived is False


def test_order_beds_by_name(base_store: Store):
    """Test return bed ordered by name."""
    # GIVEN a store containing bed
    # WHEN retrieving a beds
    beds: List[Bed] = order_beds_by_name(beds=base_store._get_bed_query())

    # THEN a bed should be returned
    assert beds

    # THEN the bed attribute is_archived should be False
    assert beds[0].name == "Bed"
