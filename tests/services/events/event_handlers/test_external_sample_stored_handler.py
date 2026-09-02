from unittest.mock import create_autospec

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.store.models import Case, Sample
from cg.store.store import Store


def test_handle_starts_case():
    # GIVEN a valid event payload
    event_payload: dict = {"status_db.sample_internal_id": "ACC123"}

    # GIVEN that the sample belongs to a purely external case
    status_db: Store = create_autospec(Store)
    case: Case = create_autospec(Case)
    sample: Sample = create_autospec(Sample, case_that_delivers=case, is_external=True)
    case.samples = [sample]

    # GIVEN that all samples in the case are stored
    hk_api: HousekeeperAPI = create_autospec(HousekeeperAPI)

    # GIVEN that starting the case goes well

    # WHEN handling the event

    # THEN we should have checked that all samples were indeed stored

    # THEN the case was started

    pass
