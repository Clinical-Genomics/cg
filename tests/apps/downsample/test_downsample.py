"""Tests for the DownsampleAPI."""
from cg.apps.downsample.downsample import DownSampleAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.models.downsample.downsample_data import DownsampleData
from cg.store import Store


def test_add_downsampled_sample_entry_to_statusdb(downsample_api: DownSampleAPI) -> None:
    """Test to add the downsampled sample entry to StatusDB."""
    # GIVEN a DownsampleAPI

    # WHEN adding a downsampled case to statusDB
    downsample_api.add_downsampled_case_to_statusdb()

    # THEN a downsampled case is added to the store
    assert downsample_api.status_db.get_case_by_name(
        downsample_api.downsample_data.downsampled_case.name
    )
