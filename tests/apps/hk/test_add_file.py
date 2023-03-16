""" Test adding files with Housekeeper API."""
from pathlib import Path
from typing import Dict, Any

from tests.mocks.hk_mock import MockHousekeeperAPI
from tests.store_helpers import StoreHelpers


def test_add_file_with_flat_tag(
    hk_tag: str,
    housekeeper_api: MockHousekeeperAPI,
    helpers: StoreHelpers,
    hk_bundle_data: Dict[str, Any],
    fastq_file: Path,
):
    """Test that we can call hk with one existing tag."""

    # GIVEN a hk api populated with a version obj
    version_obj = helpers.ensure_hk_version(housekeeper_api, hk_bundle_data)

    # GIVEN a tag that is just a string that exists
    assert housekeeper_api.get_tag(hk_tag)

    # WHEN we call add_file
    new_file = housekeeper_api.add_file(fastq_file, version_obj, hk_tag)

    # THEN the file should have been added to hk
    assert new_file


def test_add_file_with_list_of_tags(
    housekeeper_api: MockHousekeeperAPI,
    helpers: StoreHelpers,
    hk_bundle_data: Dict[str, Any],
    fastq_file: Path,
    not_existing_hk_tag: str,
):
    """Test that we can call Housekeeper with more than one tag."""

    # GIVEN a hk api populated with a version obj
    version_obj = helpers.ensure_hk_version(housekeeper_api, hk_bundle_data)

    # GIVEN a list of tags that does not exist
    tags = [not_existing_hk_tag, not_existing_hk_tag + "_2"]
    for tag_name in tags:
        assert housekeeper_api.get_tag(tag_name) is None

    # WHEN we call add_file
    new_file = housekeeper_api.add_file(fastq_file, version_obj, tags)

    # THEN the file should have been added to Housekeeper
    assert new_file
