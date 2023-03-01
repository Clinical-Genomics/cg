from typing import Optional

from sqlalchemy.orm import Query

from cg.store import Store
from cg.store.models import Bed, BedVersion


def test_get_bed_query(base_store: Store):
    """Test function to return the bed query."""

    # GIVEN a store with bed records

    # WHEN getting the query for the flow cells
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
