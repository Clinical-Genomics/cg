from typing import List

from cg.store import Store
from cg.store.models import BedVersion
from cg.store.status_bed_version_filters import get_bed_version_by_short_name


def test_get_bed_version_by_short_name(base_store: Store, bed_version_short_name: str):
    """Test return bed version by short name."""
    # GIVEN a store containing bed version

    # WHEN retrieving bed versions
    bed_versions: List[BedVersion] = get_bed_version_by_short_name(
        bed_versions=base_store._get_bed_version_query(),
        bed_version_short_name=bed_version_short_name,
    )

    # THEN bed version should be returned
    assert bed_versions

    # THEN the short name should match the original
    assert bed_versions[0].shortname == bed_version_short_name


def test_get_bed_version_by_short_name_when_no_name(base_store: Store, bed_version_short_name: str):
    """Test return bed version by short name when short name does not exist."""
    # GIVEN a store containing bed version

    # WHEN retrieving bed versions
    bed_versions: List[BedVersion] = get_bed_version_by_short_name(
        bed_versions=base_store._get_bed_version_query(), bed_version_short_name="does_not_exist"
    )

    # THEN bed versions should not be returned
    assert not list(bed_versions)
