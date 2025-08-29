from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import Priority, Workflow
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.services.analysis_starter.tracker.implementations import mip_dna as mip_dna_tracker
from cg.services.analysis_starter.tracker.implementations.mip_dna import MIPDNATracker
from cg.store.models import Analysis, Case
from cg.store.store import Store


@pytest.mark.freeze_time
def test_track(mocker: MockerFixture):
    # GIVEN a case
    case_id = "some_case"
    case: Case = create_autospec(Case, data_analysis=Workflow.MIP_DNA, priority=Priority.standard)

    # GIVEN an analysis
    analysis: Analysis = create_autospec(Analysis)

    # GIVEN a StatusDB mock
    mock_status_db: Store = create_autospec(Store)
    mock_status_db.get_case_by_internal_id = Mock(return_value=case)
    mock_status_db.add_analysis = Mock(return_value=analysis)

    # GIVEN a mock TrailblazerAPI
    mock_trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)
    mock_trailblazer_api.add_pending_analysis = Mock(
        return_value=TrailblazerAnalysis(
            id=1, logged_at=None, started_at=None, completed_at=None, out_dir=None, config_path=None
        )
    )

    # GIVEN MIP-DNA tracker
    workflow_root = "/some/root"
    tracker = MIPDNATracker(
        store=mock_status_db, trailblazer_api=mock_trailblazer_api, workflow_root=workflow_root
    )

    # GIVEN MIP-DNA case config
    case_config = MIPDNACaseConfig(
        case_id=case_id,
        email="some_email",
        slurm_qos="some_qos",
    )

    # GIVEN that there is a qc info file with the mip version
    mocker.patch.object(mip_dna_tracker, "read_yaml", return_value={"mip_version": "v8.2.5"})

    # GIVEN an email
    email = "email@scilifelab.se"
    mocker.patch.object(mip_dna_tracker, "environ_mail", return_value=email)

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
    assert analysis.case == case

    # THEN the items are added to the database
    mock_status_db.add_item_to_store.assert_called_with(analysis)
    mock_status_db.commit_to_store.assert_called_once()

    # THEN analysis object should have been created in Trailblazer
    mock_trailblazer_api.add_pending_analysis.assert_called_with(
        analysis_type=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
        case_id=case_id,
        config_path=Path(workflow_root, case_id, "analysis", "slurm_job_ids.yaml"),
        email=email,
        order_id=order_id,
        out_dir=out_dir,
        priority=priority,
        ticket=ticket,
        workflow=self.store.get_case_workflow(case_id),
        workflow_manager=self._workflow_manager(),
        tower_workflow_id=tower_workflow_id,
        is_hidden=is_case_for_development,
    )
