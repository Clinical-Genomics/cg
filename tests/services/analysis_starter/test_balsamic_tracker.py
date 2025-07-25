from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest

from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import Workflow
from cg.services.analysis_starter.configurator.models.balsamic import BalsamicCaseConfig
from cg.services.analysis_starter.tracker.implementations.balsamic import BalsamicTracker
from cg.store.models import Analysis
from cg.store.store import Store


@pytest.fixture
def balsamic_tracker(balsamic_store: Store, tmp_path: Path) -> BalsamicTracker:
    balsamic_root = tmp_path / "balsamic"
    balsamic_root.mkdir(parents=True, exist_ok=True)
    trailblazer_api: Mock[TrailblazerAPI] = create_autospec(TrailblazerAPI)
    return BalsamicTracker(
        store=balsamic_store,
        trailblazer_api=trailblazer_api,
        workflow_root=str(balsamic_root),
    )


def test_balsamic_tracker_successful(
    balsamic_case_config: BalsamicCaseConfig,
    balsamic_tracker: BalsamicTracker,
):
    # GIVEN a valid Balsamic case config

    # GIVEN that a Balsamic Config file exists
    balsamic_case_config.sample_config.parent.mkdir()
    with open(balsamic_case_config.sample_config, "w") as file:
        file.write('{"analysis": {"BALSAMIC_version": "1.0.12"}}')

    balsamic_tracker.trailblazer_api.add_pending_analysis = Mock(
        return_value=create_autospec(TrailblazerAnalysis, id=11234)
    )
    balsamic_tracker.track(case_config=balsamic_case_config)
    # WHEN tracking the analysis

    # THEN trailblazer API should be called with the correct parameters
    balsamic_tracker.trailblazer_api.add_pending_analysis.assert_called_once()

    # THEN the analysis should be created in the status database
    created_analysis: Analysis = balsamic_tracker.store.get_latest_started_analysis_for_case(
        case_id=balsamic_case_config.case_id,
    )
    assert created_analysis.workflow == Workflow.BALSAMIC
    assert created_analysis.workflow_version == "1.0.12"
