from unittest.mock import Mock, create_autospec

from cg.apps.tb import TrailblazerAPI
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.services.analysis_starter.tracker.implementations.mip_dna import MIPDNATracker
from cg.store.models import Case
from cg.store.store import Store


def test_track():
    # GIVEN a StatusDB mock
    mock_status_db: Store = create_autospec(Store)
    mock_status_db.get_case_by_internal_id = Mock(return_value=create_autospec(Case))

    # GIVEN a mock TrailblazerAPI
    mock_trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)

    # GIVEN MIP-DNA tracker
    tracker = MIPDNATracker(
        store=mock_status_db, trailblazer_api=mock_trailblazer_api, workflow_root="/some/root"
    )

    # GIVEN MIP-DNA case config
    case_config = MIPDNACaseConfig(
        case_id="some_case",
        email="some_email",
        slurm_qos="some_qos",
    )

    # WHEN calling track
    tracker.track(case_config=case_config)

    # THEN analysis object should have been created in StatusDB
    mock_status_db.add_analysis.assert_called_with()

    # THEN analysis object should have been created in Trailblazer
