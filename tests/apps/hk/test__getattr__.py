""" Test the __getattr__ override when calling private _store """

import logging


def test_calling_method_on_private_store_give_warning(housekeeper_api, caplog):
    """Test that we get a log warning for unwrapped methods"""

    # GIVEN an hk api and a method that is not wrapped
    caplog.set_level(logging.INFO)

    # WHEN we call add_file
    housekeeper_api.file_("")

    # THEN the log should contain a warning that we have called something non-wrapped
    with caplog.at_level(logging.INFO):
        assert "file_" in caplog.text
        assert "HousekeeperAPI" in caplog.text
