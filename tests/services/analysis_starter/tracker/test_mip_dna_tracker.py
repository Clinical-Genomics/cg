from datetime import datetime
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import Priority, Workflow
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.services.analysis_starter.tracker.implementations.mip_dna import MIPDNATracker
from cg.store.models import Case
from cg.store.store import Store


@pytest.mark.freeze_time
def test_track(mocker: MockerFixture):
    # GIVEN a case
    case: Case = create_autospec(Case, data_analysis=Workflow.MIP_DNA, priority=Priority.standard)

    # GIVEN a StatusDB mock
    mock_status_db: Store = create_autospec(Store)
    mock_status_db.get_case_by_internal_id = Mock(return_value=case)

    # GIVEN a mock TrailblazerAPI
    mock_trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)
    mock_trailblazer_api.add_pending_analysis = Mock(
        return_value=TrailblazerAnalysis(
            id=1, logged_at=None, started_at=None, completed_at=None, out_dir=None, config_path=None
        )
    )

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
    mock_status_db.add_analysis.assert_called_with(
        completed_at=None,
        primary=True,
        started_at=datetime.now(),
        trailblazer_id=1,
        version="v8.2.5",
        workflow=Workflow.MIP_DNA,
    )

    # THEN analysis object should have been created in Trailblazer
