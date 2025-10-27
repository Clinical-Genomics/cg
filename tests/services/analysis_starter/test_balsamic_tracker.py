from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture, MockFixture

from cg.apps.environ import environ_email
from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import Workflow
from cg.constants.constants import WorkflowManager
from cg.constants.priority import Priority, SlurmQos, TrailblazerPriority
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.constants.tb import AnalysisType
from cg.services.analysis_starter.configurator.models.balsamic import BalsamicCaseConfig
from cg.services.analysis_starter.tracker import tracker as parent_tracker
from cg.services.analysis_starter.tracker.implementations import balsamic
from cg.services.analysis_starter.tracker.implementations.balsamic import BalsamicTracker
from cg.store.models import Analysis, Case, Customer, Order, Sample
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
    mocker.patch.object(
        balsamic,
        "read_json",
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


# TODO: See if we could parametrise with the mip test


@pytest.mark.parametrize(
    "customer_id, should_be_hidden",
    [("cust000", True), ("cust666", False)],
    ids=["internal", "non-internal"],
)
@pytest.mark.freeze_time
def test_track(customer_id: str, should_be_hidden: bool, mocker: MockerFixture):
    # GIVEN a Balsamic case tied to an order
    case_id = "some_case"
    case: Case = create_autospec(
        Case,
        customer=create_autospec(Customer, internal_id=customer_id),
        data_analysis=Workflow.BALSAMIC,
        priority=Priority.standard,
        latest_order=create_autospec(Order, id=2),
        samples=[
            create_autospec(Sample, prep_category=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING)
        ],
    )

    # GIVEN an analysis
    analysis: Analysis = create_autospec(Analysis)

    # GIVEN a StatusDB mock
    mock_status_db: Store = create_autospec(Store)
    mock_status_db.get_case_by_internal_id = Mock(return_value=case)
    mock_status_db.add_analysis = Mock(return_value=analysis)
    mock_status_db.get_latest_ticket_from_case = Mock(return_value="123456")
    mock_status_db.get_case_workflow = Mock(return_value=Workflow.BALSAMIC)

    # GIVEN a mock TrailblazerAPI
    mock_trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)
    mock_trailblazer_api.add_pending_analysis = Mock(
        return_value=TrailblazerAnalysis(
            id=1, logged_at=None, started_at=None, completed_at=None, out_dir=None, config_path=None
        )
    )

    # GIVEN MIP-DNA tracker
    workflow_root = "/some/root"
    tracker = BalsamicTracker(
        store=mock_status_db, trailblazer_api=mock_trailblazer_api, workflow_root=workflow_root
    )

    # GIVEN MIP-DNA case config
    # case_config = MIPDNACaseConfig(
    #     case_id=case_id,
    #     conda_binary="conda/binary",
    #     conda_environment="conda_env",
    #     email="some_email",
    #     pipeline_binary="pipeline/binary",
    #     pipeline_command="analyse rd_dna",
    #     pipeline_config_path="some/path",
    #     slurm_qos=SlurmQos.NORMAL,
    #     use_bwa_mem=False,
    # )

    case_config = BalsamicCaseConfig(
        account="development",
        binary=Path("bin, balsamic"),
        case_id=case_id,
        conda_binary=Path("bin", "conda"),
        environment="T_BALSAMIC",
        head_job_partition="head-jobs",
        qos=SlurmQos.NORMAL,
        sample_config=Path("tmp_path", case_id, f"{case_id}.json"),
        workflow=Workflow.BALSAMIC,
    )

    # GIVEN that there is a qc info file with the mip version
    balsamic_version = "v18.0.0"
    mocker.patch.object(
        balsamic,
        "read_json",
        return_value={"analysis": {"BALSAMIC_version": balsamic_version}},
    )

    # GIVEN an email
    email = "email@scilifelab.se"
    mocker.patch.object(parent_tracker, "environ_email", return_value=email)

    # WHEN calling track
    tracker.track(case_config=case_config)

    # THEN analysis object should have been created in StatusDB
    mock_status_db.add_analysis.assert_called_with(
        completed_at=None,
        primary=True,
        started_at=datetime.now(),
        trailblazer_id=1,
        version=balsamic_version,
        workflow=Workflow.BALSAMIC,
    )
    assert analysis.case == case

    # THEN the items are added to the database
    mock_status_db.add_item_to_store.assert_called_with(analysis)
    mock_status_db.commit_to_store.assert_called_once()

    out_dir = Path(workflow_root, case_id, "analysis")

    # THEN analysis object should have been created in Trailblazer
    mock_trailblazer_api.add_pending_analysis.assert_called_with(
        analysis_type=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
        case_id=case_id,
        config_path=Path(out_dir, "slurm_job_ids.yaml").as_posix(),
        email=email,
        order_id=2,
        out_dir=out_dir.as_posix(),
        priority=TrailblazerPriority.NORMAL,
        ticket="123456",
        workflow=Workflow.BALSAMIC,
        workflow_manager=WorkflowManager.Slurm,
        tower_workflow_id=None,
        is_hidden=should_be_hidden,
    )
