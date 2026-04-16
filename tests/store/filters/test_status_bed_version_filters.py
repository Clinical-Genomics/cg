from cg.store.filters.status_bed_version_filters import filter_bed_version_by_file_name
from cg.store.models import BedVersion
from cg.store.store import Store


def test_get_bed_version_by_file_name(base_store: Store, bed_version_file_name: str):
    """Test return bed version by file name."""
    # GIVEN a store containing bed version

    # WHEN retrieving bed version
    bed_version: BedVersion = filter_bed_version_by_file_name(
        bed_versions=base_store._get_query(table=BedVersion),
        bed_version_file_name=bed_version_file_name,
    ).first()

    # THEN bed version should be returned
    assert bed_version

    # THEN the file name should match the original
    assert bed_version.filename == bed_version_file_name
