from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import Priority, Workflow
from cg.constants.constants import WorkflowManager
from cg.constants.priority import SlurmQos, TrailblazerPriority
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.services.analysis_starter.tracker import tracker as parent_tracker
from cg.services.analysis_starter.tracker.implementations import mip_dna as mip_dna_tracker
from cg.services.analysis_starter.tracker.implementations.mip_dna import MIPDNATracker
from cg.store.models import Analysis, Case, Customer, Order, Sample
from cg.store.store import Store


@pytest.mark.parametrize(
    "customer_id, should_be_hidden",
    [("cust000", True), ("cust666", False)],
    ids=["internal", "non-internal"],
)
@pytest.mark.freeze_time
def test_track(customer_id: str, should_be_hidden: bool, mocker: MockerFixture):
    # GIVEN a case tied to an order
    case_id = "some_case"
    case: Case = create_autospec(
        Case,
        customer=create_autospec(Customer, internal_id=customer_id),
        data_analysis=Workflow.MIP_DNA,
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
    mock_status_db.get_case_by_internal_id_strict = Mock(return_value=case)
    mock_status_db.add_analysis = Mock(return_value=analysis)
    mock_status_db.get_latest_ticket_from_case = Mock(return_value="123456")
    mock_status_db.get_case_workflow = Mock(return_value=Workflow.MIP_DNA)

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
        conda_binary="conda/binary",
        conda_environment="conda_env",
        email="some_email",
        pipeline_binary="pipeline/binary",
        pipeline_command="analyse rd_dna",
        pipeline_config_path="some/path",
        slurm_qos=SlurmQos.NORMAL,
        use_bwa_mem=False,
    )

    # GIVEN that there is a qc info file with the mip version
    mip_version = "v8.2.5"
    mocker.patch.object(mip_dna_tracker, "read_yaml", return_value={"mip_version": mip_version})

    # GIVEN an email
    email = "email@scilifelab.se"
    mocker.patch.object(parent_tracker, "environ_email", return_value=email)

    # WHEN calling track
    tracker.track(case_config=case_config)

    # THEN analysis object should have been created in StatusDB
    mock_status_db.add_analysis.assert_called_with(
        completed_at=None,
        primary=True,
        session_id=None,
        started_at=datetime.now(),
        trailblazer_id=1,
        version=mip_version,
        workflow=Workflow.MIP_DNA,
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
        workflow=Workflow.MIP_DNA,
        workflow_manager=WorkflowManager.Slurm,
        tower_workflow_id=None,
        is_hidden=should_be_hidden,
    )
