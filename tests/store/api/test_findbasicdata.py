from typing import Optional

from sqlalchemy.orm import Query

from cg.store import Store
from cg.store.models import Bed, BedVersion, Collaboration, Organism


def test_get_bed_query(base_store: Store):
    """Test function to return the bed query."""

    # GIVEN a store with bed records

    # WHEN getting the query for the beds
    bed_query: Query = base_store._get_bed_query()

    # THEN a query should be returned
    assert isinstance(bed_query, Query)


def test_get_beds(base_store: Store):
    """Test returning bed records query."""

    # GIVEN a store with beds

    # WHEN fetching beds
    beds: Query = base_store.get_beds()

    # THEN beds should have be returned
    assert beds


def test_get_active_beds(base_store: Store):
    """Test returning not archived bed records from the database."""

    # GIVEN a store with beds

    # WHEN fetching beds
    beds: Query = base_store.get_active_beds()

    # THEN beds should have be returned
    assert beds

    # THEN the bed records should not be archived
    for bed in beds:
        assert bed.is_archived is False


def test_get_active_beds_when_archived(base_store: Store):
    """Test returning not archived bed records from the database when archived."""

    # GIVEN a store with beds
    beds: Query = base_store.get_active_beds()
    for bed in beds:
        bed.is_archived = True
        base_store.add_commit(bed)

    # WHEN fetching beds
    active_beds: Query = base_store.get_active_beds()

    # THEN return no beds
    assert not list(active_beds)


def test_get_bed_by_name(base_store: Store, bed_name: str):
    """Test returning a bed record by name from the database."""

    # GIVEN a store with beds

    # WHEN fetching beds
    bed: Optional[Bed] = base_store.get_bed_by_name(bed_name=bed_name)

    # THEN return a bed
    assert bed

    # THEN return a bed with the supplied bed name
    assert bed.name == bed_name


def test_get_bed_by_name_when_no_match(base_store: Store):
    """Test returning a bed record by name from the database when no match."""

    # GIVEN a store with beds

    # WHEN fetching beds
    bed: Optional[Bed] = base_store.get_bed_by_name(bed_name="does_not_exist")

    # THEN do not return a bed
    assert not bed


def test_get_latest_bed_version(base_store: Store, bed_name: str):
    """Test returning a bed version by bed name from the database."""

    # GIVEN a store with beds

    # WHEN fetching beds
    bed_version: BedVersion = base_store.get_latest_bed_version(bed_name=bed_name)

    # THEN return a bed version with the supplied bed name
    assert bed_version.version == 1


def test_get_bed_version_query(base_store: Store):
    """Test function to return the bed version query."""

    # GIVEN a store with bed versions records

    # WHEN getting the query for the bed versions
    bed_version_query: Query = base_store._get_bed_version_query()

    # THEN a query should be returned
    assert isinstance(bed_version_query, Query)


def test_get_bed_version_by_short_name(base_store: Store, bed_version_short_name: str):
    """Test function to return the bed version by short name."""

    # GIVEN a store with bed versions records

    # WHEN getting the query for the bed versions
    bed_version: BedVersion = base_store.get_bed_version_by_short_name(
        bed_version_short_name=bed_version_short_name
    )

    # THEN return a bed version with the supplied bed version short name
    assert bed_version.shortname == bed_version_short_name


def test_get_collaboration_by_internal_id(base_store: Store, collaboration_id: str):
    """Test function to return the collaborations by internal_id."""

    # GIVEN a store with collaborations

    # WHEN getting the query for the collaborations
    collaboration: Collaboration = base_store.get_collaboration_by_internal_id(
        internal_id=collaboration_id
    )

    # THEN return a collaboration with the give collaboration internal_id
    assert collaboration.internal_id == collaboration_id


def test_get_organism_by_internal_id_returns_correct_organism(store_with_organisms: Store):
    """Test finding an organism by internal ID when the ID exists."""

    # GIVEN a store with multiple organisms
    num_organisms = store_with_organisms._get_organism_query().count()
    assert num_organisms > 0

    # Select a random organism from the store
    organism = store_with_organisms.query(Organism).first()
    assert isinstance(organism, Organism)

    # WHEN finding the organism by internal ID
    internal_id = organism.internal_id
    filtered_organism = store_with_organisms.get_organism_by_internal_id(internal_id)

    # THEN the filtered organism should be of the correct instance and have the correct internal ID
    assert isinstance(filtered_organism, Organism)
    assert filtered_organism.internal_id == internal_id


def test_get_organism_by_internal_id_returns_none_when_id_does_not_exist(
    store_with_organisms: Store,
):
    """Test finding an organism by internal ID when the ID does not exist."""

    # GIVEN a store with multiple organisms
    num_organisms = store_with_organisms._get_organism_query().count()
    assert num_organisms > 0

    # Choose an ID that does not exist in the database
    non_existent_id = "non_existent_id"

    # WHEN finding the organism by internal ID
    filtered_organism = store_with_organisms.get_organism_by_internal_id(non_existent_id)

    # THEN the filtered organism should be None
    assert filtered_organism is None
