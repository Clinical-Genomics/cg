from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture
from typed_mock import TypedMock, create_typed_mock

from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import Workflow
from cg.constants.constants import WorkflowManager
from cg.constants.priority import Priority, SlurmQos, TrailblazerPriority
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.services.analysis_starter.configurator.models.balsamic import BalsamicCaseConfig
from cg.services.analysis_starter.configurator.models.mip_dna import MIPDNACaseConfig
from cg.services.analysis_starter.tracker import tracker as parent_tracker
from cg.services.analysis_starter.tracker.implementations import balsamic
from cg.services.analysis_starter.tracker.implementations import mip_dna as mip_dna_tracker
from cg.services.analysis_starter.tracker.implementations.balsamic import BalsamicTracker
from cg.services.analysis_starter.tracker.implementations.mip_dna import MIPDNATracker
from cg.services.analysis_starter.tracker.tracker import Tracker
from cg.store.models import Analysis, Case, Customer, Order, Sample
from cg.store.store import Store

BALSAMIC_VERSION = "v18.0.0"
MIP_DNA_VERSION = "v8.2.5"


@pytest.fixture(autouse=True)
def mock_readers(mocker: MockerFixture):
    """Mocks the file readers for all pipelines."""
    with (
        mocker.patch.object(
            balsamic,
            "read_json",
            return_value={"analysis": {"BALSAMIC_version": BALSAMIC_VERSION}},
        ),
        mocker.patch.object(
            mip_dna_tracker, "read_yaml", return_value={"mip_version": MIP_DNA_VERSION}
        ),
    ):
        yield


@pytest.fixture
def case_id() -> str:
    return "case_id"


@pytest.fixture
def balsamic_case_config(case_id: str) -> BalsamicCaseConfig:
    return BalsamicCaseConfig(
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


@pytest.fixture
def mip_dna_case_config(case_id: str) -> MIPDNACaseConfig:
    return MIPDNACaseConfig(
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


@pytest.fixture
def tracker_scenario(
    balsamic_case_config: BalsamicCaseConfig, mip_dna_case_config: MIPDNACaseConfig
) -> dict:
    return {
        Workflow.BALSAMIC: (
            BalsamicTracker,
            balsamic_case_config,
            "slurm_jobids.yaml",
            BALSAMIC_VERSION,
        ),
        Workflow.MIP_DNA: (
            MIPDNATracker,
            mip_dna_case_config,
            "slurm_job_ids.yaml",
            MIP_DNA_VERSION,
        ),
    }


@pytest.mark.parametrize("workflow", [Workflow.BALSAMIC, Workflow.MIP_DNA])
@pytest.mark.parametrize(
    "customer_id, should_be_hidden",
    [("cust000", True), ("cust666", False)],
    ids=["internal", "non-internal"],
)
@pytest.mark.freeze_time
def test_track(
    case_id: str,
    customer_id: str,
    should_be_hidden: bool,
    tracker_scenario: dict,
    workflow: Workflow,
    mocker: MockerFixture,
):
    """
    Test that analyses are correctly tracked for SLURM pipelines.
    It tests two scenarios per workflow:
        Creating one Trailblazer analysis that should be hidden and one that should not.
    """
    # GIVEN the tracker class, case config, job ids file name and version for the workflow
    tracker_class, case_config, job_ids_filename, pipeline_version = tracker_scenario[workflow]

    # GIVEN a case tied to an order
    case: Case = create_autospec(
        Case,
        customer=create_autospec(Customer, internal_id=customer_id),
        data_analysis=workflow,
        priority=Priority.standard,
        latest_order=create_autospec(Order, id=2),
        samples=[
            create_autospec(Sample, prep_category=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING)
        ],
    )

    # GIVEN an analysis
    analysis: Analysis = create_autospec(Analysis)

    # GIVEN a StatusDB instance
    status_db: TypedMock[Store] = create_typed_mock(Store)
    status_db.as_type.get_case_by_internal_id = Mock(return_value=case)
    status_db.as_type.add_analysis = Mock(return_value=analysis)
    status_db.as_type.get_latest_ticket_from_case = Mock(return_value="123456")
    status_db.as_type.get_case_workflow = Mock(return_value=workflow)

    # GIVEN a TrailblazerAPI
    trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)
    trailblazer_api.add_pending_analysis = Mock(
        return_value=TrailblazerAnalysis(
            id=1, logged_at=None, started_at=None, completed_at=None, out_dir=None, config_path=None
        )
    )

    # GIVEN a pipeline-specific tracker
    workflow_root = "/some/root"
    tracker: Tracker = tracker_class(
        store=status_db, trailblazer_api=trailblazer_api, workflow_root=workflow_root
    )

    # GIVEN an email
    email = "email@scilifelab.se"
    mocker.patch.object(parent_tracker, "environ_email", return_value=email)

    # WHEN calling track
    tracker.track(case_config=case_config)

    # THEN analysis object should have been created in StatusDB
    status_db.as_mock.add_analysis.assert_called_with(
        completed_at=None,
        primary=True,
        started_at=datetime.now(),
        trailblazer_id=1,
        version=pipeline_version,
        workflow=workflow,
    )
    assert analysis.case == case

    # THEN the items are added to the database
    status_db.as_mock.add_item_to_store.assert_called_with(analysis)
    status_db.as_mock.commit_to_store.assert_called_once()

    out_dir = Path(workflow_root, case_id, "analysis")

    # THEN analysis object should have been created in Trailblazer
    trailblazer_api.add_pending_analysis.assert_called_with(
        analysis_type=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
        case_id=case_id,
        config_path=Path(out_dir, job_ids_filename).as_posix(),
        email=email,
        order_id=2,
        out_dir=out_dir.as_posix(),
        priority=TrailblazerPriority.NORMAL,
        ticket="123456",
        workflow=workflow,
        workflow_manager=WorkflowManager.Slurm,
        tower_workflow_id=None,
        is_hidden=should_be_hidden,
    )
