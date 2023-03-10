from cg.store.api.core import Store
from cg.store.models import Organism
from cg.store.organism_filters import filter_organism_by_internal_id


def test_filter_organism_by_internal_id_returns_correct_organism(store_with_organisms: Store):
    """Test filtering an organism by internal ID when the ID exists."""

    # GIVEN a store with multiple organisms
    num_organisms = store_with_organisms._get_organism_query().count()
    assert num_organisms > 0

    # Select a random organism from the store
    organism = store_with_organisms.query(Organism).first()
    assert isinstance(organism, Organism)

    # WHEN filtering the organisms by internal ID
    internal_id = organism.internal_id

    filtered_organisms = filter_organism_by_internal_id(
        organisms=store_with_organisms._get_organism_query(), internal_id=internal_id
    ).all()

    # THEN only one organism should be returned with the correct internal ID
    assert len(filtered_organisms) == 1
    assert isinstance(filtered_organisms[0], Organism)
    assert filtered_organisms[0].internal_id == internal_id


def test_filter_organism_by_internal_id_returns_empty_list_when_id_does_not_exist(
    store_with_organisms: Store,
):
    """Test filtering an organism by internal ID when the ID does not exist."""

    # GIVEN a store with multiple organisms
    num_organisms = store_with_organisms._get_organism_query().count()
    assert num_organisms > 0

    # Choose an ID that does not exist in the database
    non_existent_id = "non_existent_id"

    # WHEN filtering the organisms by internal ID
    filtered_organisms = filter_organism_by_internal_id(
        organisms=store_with_organisms._get_organism_query(), internal_id=non_existent_id
    ).all()

    # THEN the filtered organisms should be an empty list
    assert len(filtered_organisms) == 0
