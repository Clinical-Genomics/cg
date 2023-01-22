""" Test the __getattr__ override when calling private _store."""

import logging

from tests.mocks.hk_mock import MockHousekeeperAPI


def test_calling_method_on_private_store_give_warning(housekeeper_api: MockHousekeeperAPI, caplog):
    """Test that we get a log warning for unwrapped methods."""

    # GIVEN an hk api and a method that is not wrapped
    caplog.set_level(logging.WARNING)

    # WHEN we call add_file
    housekeeper_api.files_before()

    # THEN the log should contain a warning that we have called something non-wrapped
    with caplog.at_level(logging.WARNING):
        assert "files_before" in caplog.text
        assert "HousekeeperAPI" in caplog.text
