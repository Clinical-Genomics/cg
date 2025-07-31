from pathlib import Path

import mock
import pytest

from cg.apps.environ import environ_email
from cg.apps.tb import TrailblazerAPI
from cg.constants.constants import Workflow, WorkflowManager
from cg.constants.tb import AnalysisType
from cg.models.cg_config import CGConfig
from cg.models.orders.sample_base import StatusEnum
from cg.services.analysis_starter.configurator.models.nextflow import NextflowCaseConfig
from cg.services.analysis_starter.tracker.implementations.nextflow import NextflowTracker
from cg.store.models import Case, CaseSample, Customer, Order
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


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


def test_nextflow_tracker(nextflow_tracker: NextflowTracker, raredisease_case_id: str):
    # GIVEN a raredisease case
    case: Case = nextflow_tracker.store.get_case_by_internal_id(raredisease_case_id)
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

    # WHEN wanting to track the started microSALT analysis
    with mock.patch.object(
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
    ) as request_submitter:
        nextflow_tracker.track(case_config=case_config, tower_workflow_id="1")

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
        "ticket": str(case.latest_order.ticket_id),
        "workflow_manager": WorkflowManager.Tower,
        "tower_workflow_id": "1",
        "is_hidden": True,
    }
    request_submitter.assert_called_with(
        command="add-pending-analysis", request_body=expected_request_body
    )
