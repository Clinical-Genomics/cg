from unittest.mock import create_autospec

from cg.services.analysis_starter.tracker.implementations.mip-dna import MIPDNATracker
from cg.store.store import Store
from tests.services.analysis_starter.test_mip_dna_configurator import mock_status_db


def test_track():
    # GIVEN a StatusDB mock
    mock_status_db: Store = create_autospec(Store)

    # GIVEN MIP-DNA tracker
    tracker = MIPDNATracker(store=mock_status_db)

    # GIVEN MIP-DNA case config
    # WHEN calling track
    tracker.track()

    # THEN analysis object should have been created in StatusDB
    mock_status_db.add_analysis.assert_called_with()


    # THEN analysis object should have been created in Trailblazer

