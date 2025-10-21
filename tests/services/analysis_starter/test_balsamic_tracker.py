from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockFixture

from cg.apps.environ import environ_email
from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import Workflow
from cg.constants.constants import WorkflowManager
from cg.constants.priority import TrailblazerPriority
from cg.constants.tb import AnalysisType
from cg.services.analysis_starter.configurator.models.balsamic import BalsamicCaseConfig
from cg.services.analysis_starter.tracker.implementations.balsamic import BalsamicTracker
from cg.store.models import Analysis, Case
from cg.store.store import Store


@pytest.fixture
def balsamic_tracker(balsamic_store: Store, tmp_path: Path) -> BalsamicTracker:
    balsamic_root = tmp_path / "balsamic"
    balsamic_root.mkdir(parents=True, exist_ok=True)
    trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)
    return BalsamicTracker(
        store=balsamic_store,
        trailblazer_api=trailblazer_api,
        workflow_root=str(balsamic_root),
    )


def test_balsamic_tracker_successful(
    balsamic_case_config: BalsamicCaseConfig,
    balsamic_tracker: BalsamicTracker,
    mocker: MockFixture,
):
    # GIVEN a valid Balsamic case config

    # GIVEN that the case exists in the database
    db_case: Case = balsamic_tracker.store.get_case_by_internal_id(balsamic_case_config.case_id)

    # GIVEN that a Balsamic Config file exists
    mocker.patch(
        "cg.services.analysis_starter.tracker.implementations.balsamic.read_json",
        return_value={"analysis": {"BALSAMIC_version": "1.0.12"}},
    )

    balsamic_tracker.trailblazer_api.add_pending_analysis = Mock(
        return_value=create_autospec(TrailblazerAnalysis, id=11234)
    )

    # GIVEN the expected request body for Trailblazer
    expected_request_body: dict = {
        "case_id": balsamic_case_config.case_id,
        "email": environ_email(),
        "analysis_type": AnalysisType.TGS.value,
        "config_path": Path(
            balsamic_tracker.workflow_root,
            f"{balsamic_case_config.case_id}",
            "analysis",
            "slurm_jobids.yaml",
        ).as_posix(),
        "order_id": db_case.latest_order.id,
        "out_dir": Path(
            balsamic_tracker.workflow_root, f"{balsamic_case_config.case_id}", "analysis"
        ).as_posix(),
        "priority": TrailblazerPriority.NORMAL.value,
        "workflow": Workflow.BALSAMIC.value,
        "ticket": str(db_case.latest_order.ticket_id),
        "workflow_manager": WorkflowManager.Slurm.value,
        "tower_workflow_id": None,
        "is_hidden": True,
    }

    # WHEN tracking the analysis
    balsamic_tracker.track(case_config=balsamic_case_config)

    # THEN trailblazer API should be called with the correct parameters
    balsamic_tracker.trailblazer_api.add_pending_analysis.assert_called_once_with(
        **expected_request_body
    )

    # THEN the analysis should be created in the status database
    created_analysis: Analysis = balsamic_tracker.store.get_latest_started_analysis_for_case(
        case_id=balsamic_case_config.case_id,
    )
    assert created_analysis.workflow == Workflow.BALSAMIC
    assert created_analysis.workflow_version == "1.0.12"
