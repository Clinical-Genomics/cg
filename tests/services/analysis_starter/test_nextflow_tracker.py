from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest

from cg.apps.environ import environ_email
from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import Priority
from cg.constants.constants import Workflow, WorkflowManager
from cg.constants.priority import SlurmQos
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.constants.tb import AnalysisType
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.services.analysis_starter.tracker.implementations.nextflow_tracker import NextflowTracker
from cg.store.models import Case, Customer, Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.mark.freeze_time
def test_nextflow_tracker():
    # GIVEN a store with a raredisease case
    case_id = "case_id"
    ticket_id = 666666
    store: TypedMock[Store] = create_typed_mock(Store)
    sample: Sample = create_autospec(
        Sample, prep_category=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
    )
    case: Case = create_autospec(
        Case,
        customer=create_autospec(Customer, internal_id="cust000"),
        data_analysis=Workflow.RAREDISEASE,
        slurm_priority=SlurmQos.NORMAL,
        priority=Priority.standard,
        samples=[sample],
    )
    store.as_type.get_case_by_internal_id_strict = Mock(return_value=case)
    store.as_type.get_case_workflow = Mock(return_value=Workflow.RAREDISEASE)
    store.as_type.get_latest_ticket_from_case = Mock(return_value=ticket_id)

    # GIVEN a TrailblazerAPI
    trailblazer_entry_id = 123456
    tb_api: TrailblazerAPI = create_autospec(TrailblazerAPI)
    tb_submitter = tb_api.add_pending_analysis = Mock(
        return_value=create_autospec(TrailblazerAnalysis, id=trailblazer_entry_id)
    )

    # GIVEN a NextflowTracker
    nextflow_tracker = NextflowTracker(
        store=store.as_type, trailblazer_api=tb_api, workflow_root="some-root"
    )

    # GIVEN a NextflowCaseConfig for raredisease
    case_config = NextflowCaseConfig(
        case_id=case_id,
        workflow=Workflow.RAREDISEASE,
        case_priority=case.slurm_priority,
        config_profiles=[],
        nextflow_config_file="config/file",
        params_file="params/file",
        pipeline_repository="github/raredisease",
        pre_run_script="pre_run_script",
        revision="1.0.0",
        session_id="session-abc-666",
        work_dir="work/dir",
        workflow_id="1",
    )

    # WHEN wanting to track the started raredisease analysis
    nextflow_tracker.track(case_config=case_config)

    # THEN the appropriate POST should have been sent
    config_path: Path = nextflow_tracker._get_job_ids_path(case_id)
    expected_request_body: dict = {
        "analysis_type": AnalysisType.WGS,
        "case_id": case_id,
        "email": environ_email(),
        "config_path": config_path.as_posix(),
        "order_id": case.latest_order.id,
        "out_dir": config_path.parent.as_posix(),
        "priority": nextflow_tracker._get_trailblazer_priority(case_id),
        "workflow": Workflow.RAREDISEASE,
        "ticket": ticket_id,
        "workflow_manager": WorkflowManager.Tower,
        "tower_workflow_id": "1",
        "is_hidden": True,
    }
    tb_submitter.assert_called_once_with(**expected_request_body)

    # THEN an analysis was created in StatusDB
    store.as_mock.add_analysis.assert_called_once_with(
        case=case,
        completed_at=None,
        primary=True,
        session_id="session-abc-666",
        started_at=datetime.now(),
        trailblazer_id=trailblazer_entry_id,
        version="1.0.0",
        workflow=Workflow.RAREDISEASE,
    )
