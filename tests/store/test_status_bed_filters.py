from typing import List

from cg.store import Store
from cg.store.models import Bed
from cg.store.status_bed_filters import get_not_archived_beds


def test_get_not_archived_beds(base_store: Store):
    """Test return bed not archived."""
    # GIVEN a store containing bed
    # WHEN retrieving a beds not archived
    beds: List[Bed] = get_not_archived_beds(beds=base_store._get_bed_query())

    # THEN a bed should be returned
    assert beds

    # THEN the bed attribute is_archived should be False
    assert beds[0].is_archived is False
