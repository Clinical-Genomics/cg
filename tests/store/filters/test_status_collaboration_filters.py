from cg.store.filters.status_collaboration_filters import (
    filter_collaboration_by_internal_id,
)
from cg.store.models import Collaboration
from cg.store.store import Store


def test_get_collaboration_by_internal_id(base_store: Store, collaboration_id: str):
    """Test getting collaboration by internal id."""
    # GIVEN a store with a collaboration

    # WHEN retrieving the collaboration
    collaboration: Collaboration = filter_collaboration_by_internal_id(
        collaborations=base_store._get_query(table=Collaboration),
        internal_id=collaboration_id,
    ).first()

    # THEN collaboration should be returned
    assert isinstance(collaboration, Collaboration)

    # THEN the internal id should match the fixture
    assert collaboration.internal_id == collaboration_id


def test_get_collaboration_by_internal_id_wrong_name(base_store: Store, collaboration_id: str):
    """Test getting a collaboration with non-existing internal_id."""
    # GIVEN a store a collaboration

    # WHEN attempting to retrieve a non-existing collaboration
    collaboration: Collaboration = filter_collaboration_by_internal_id(
        collaborations=base_store._get_query(table=Collaboration),
        internal_id="missing_collaboration",
    ).first()

    # THEN no collaboration should be returned
    assert collaboration is None
