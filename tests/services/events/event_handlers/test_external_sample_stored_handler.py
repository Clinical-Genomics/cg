from unittest.mock import create_autospec

from cg.apps.housekeeper.hk import HousekeeperAPI


def test_handle_starts_case():
    # GIVEN a valid event payload
    event_payload: dict = {"status_db.sample_internal_id": "ACC123"}

    # GIVEN that all samples in the case are stored
    hk_api: HousekeeperAPI = create_autospec(HousekeeperAPI)

    # GIVEN that starting the case goes well

    # WHEN handling the event

    # THEN we should have checked that all samples were indeed stored

    # THEN the case was started

    pass
