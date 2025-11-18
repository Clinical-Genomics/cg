from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.apps.environ import environ_email
from cg.apps.tb import TrailblazerAPI
from cg.constants import Priority
from cg.constants.constants import Workflow, WorkflowManager
from cg.constants.priority import SlurmQos
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.constants.tb import AnalysisType
from cg.models.cg_config import CGConfig
from cg.models.orders.sample_base import StatusEnum
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.services.analysis_starter.tracker.implementations.nextflow_tracker import NextflowTracker
from cg.store.models import Case, CaseSample, Customer, Order, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.fixture
def nextflow_tracker(cg_context: CGConfig, helpers: StoreHelpers, raredisease_case_id: str):
    store: Store = cg_context.status_db
    customer: Customer = store.get_customers()[0]
    order: Order = store.add_order(customer=customer, ticket_id=1)
    store.add_item_to_store(order)
    store.commit_to_store()
    case: Case = helpers.ensure_case(
        case_id=raredisease_case_id, data_analysis=Workflow.RAREDISEASE, order=order, store=store
    )
    sample = helpers.add_sample(store=store, application_type=AnalysisType.WGS)
    case_sample: CaseSample = store.relate_sample(
        sample=sample, case=case, status=StatusEnum.unknown
    )
    store.add_multiple_items_to_store([case, sample, case_sample])
    store.commit_to_store()
    return NextflowTracker(
        store=cg_context.status_db,
        trailblazer_api=cg_context.trailblazer_api,
        workflow_root=cg_context.raredisease.root,
    )


@pytest.mark.freeze_time
def test_nextflow_tracker(
    nextflow_tracker: NextflowTracker, raredisease_case_id: str, mocker: MockerFixture
):
    # GIVEN a raredisease case
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
    store.as_type.get_latest_ticket_from_case = Mock(return_value=666666)
    nextflow_tracker.store = store.as_type
    case_config = NextflowCaseConfig(
        case_id=raredisease_case_id,
        workflow=Workflow.RAREDISEASE,
        case_priority=case.slurm_priority,
        config_profiles=[],
        nextflow_config_file="config/file",
        params_file="params/file",
        pipeline_repository="github/raredisease",
        pre_run_script="pre_run_script",
        revision="1.0.0",
        work_dir="work/dir",
    )

    # WHEN wanting to track the started raredisease analysis
    request_submitter = mocker.patch.object(
        TrailblazerAPI,
        "query_trailblazer",
        return_value={
            "id": 123456,
            "logged_at": "",
            "started_at": "",
            "completed_at": "",
            "out_dir": "",
            "config_path": "",
        },
    )
    nextflow_tracker.track(
        case_config=case_config, session_id="session-abc-666", tower_workflow_id="1"
    )

    # THEN the appropriate POST should have been sent
    config_path: Path = nextflow_tracker._get_job_ids_path(raredisease_case_id)
    expected_request_body: dict = {
        "case_id": raredisease_case_id,
        "email": environ_email(),
        "type": AnalysisType.WGS,
        "config_path": config_path.as_posix(),
        "order_id": case.latest_order.id,
        "out_dir": config_path.parent.as_posix(),
        "priority": nextflow_tracker._get_trailblazer_priority(raredisease_case_id),
        "workflow": Workflow.RAREDISEASE.upper(),
        "ticket": 666666,
        "workflow_manager": WorkflowManager.Tower,
        "tower_workflow_id": "1",
        "is_hidden": True,
    }
    request_submitter.assert_called_with(
        command="add-pending-analysis", request_body=expected_request_body
    )

    store.as_mock.add_analysis.assert_called_once_with(
        case=case,
        completed_at=None,
        primary=True,
        session_id="session-abc-666",
        started_at=datetime.now(),
        trailblazer_id=123456,
        version="1.0.0",
        workflow=Workflow.RAREDISEASE,
    )
