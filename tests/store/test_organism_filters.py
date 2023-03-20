from typing import List
from sqlalchemy.orm import Query

from cg.store.api.core import Store
from cg.store.models import Organism
from cg.store.filters.status_organism_filters import filter_organism_by_internal_id


def test_filter_organism_by_internal_id_returns_correct_organism(store_with_organisms: Store):
    """Test filtering an organism by internal ID when the ID exists."""

    # GIVEN a store with multiple organisms
    organisms: Query = store_with_organisms._get_query(table=Organism)
    assert organisms.count() > 0

    # GIVEN a random organism from the store
    organism: Organism = organisms.first()
    assert isinstance(organism, Organism)

    # WHEN filtering the organisms by internal ID
    filtered_organisms: List[Organism] = filter_organism_by_internal_id(
        organisms=organisms, internal_id=organism.internal_id
    ).all()

    # THEN only one organism should be returned
    assert len(filtered_organisms) == 1
    assert isinstance(filtered_organisms[0], Organism)

    # THEN the organism should have the same internal ID as the original organism
    assert filtered_organisms[0].internal_id == organism.internal_id


def test_filter_organism_by_internal_id_returns_empty_list_when_id_does_not_exist(
    store_with_organisms: Store, non_existent_id: str
):
    """Test filtering an organism by internal ID when the ID does not exist."""

    # GIVEN a store with multiple organisms
    organisms: Query = store_with_organisms._get_query(table=Organism)
    assert organisms.count() > 0

    # WHEN filtering the organisms by internal ID
    filtered_organisms: List[Organism] = filter_organism_by_internal_id(
        organisms=organisms, internal_id=non_existent_id
    ).all()

    # THEN the filtered organisms should be an empty list
    assert not filtered_organisms


def test_filter_organism_by_internal_id_returns_empty_list_when_id_is_none(
    store_with_organisms: Store,
):
    """Test filtering an organism by internal ID when the ID is None."""

    # GIVEN a store with multiple organisms
    organisms: Query = store_with_organisms._get_query(table=Organism)
    assert organisms.count() > 0

    # WHEN filtering the organisms by internal ID None
    filtered_organisms: List[Organism] = filter_organism_by_internal_id(
        organisms=organisms, internal_id=None
    ).all()

    # THEN the filtered organisms should be an empty list
    assert not filtered_organisms
