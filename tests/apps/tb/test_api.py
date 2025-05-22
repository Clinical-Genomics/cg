from unittest.mock import Mock, PropertyMock, create_autospec

from google.oauth2 import service_account
from requests import Response

from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants.constants import APIMethods, Workflow, WorkflowManager
from cg.constants.priority import TrailblazerPriority
from cg.constants.tb import AnalysisType
from cg.io.controller import APIRequest


def test_add_pending_analysis_succeeds(mocker):
    credentials = create_autospec(service_account.IDTokenCredentials)
    credentials.token = "some_token"
    mocker.patch.object(
        service_account.IDTokenCredentials, "from_service_account_file", return_value=credentials
    )

    id_created_by_trailblazer = 56
    successful_response = create_autospec(Response)
    successful_response.status_code = 200
    successful_response.text = (
        '{"id":'
        + str(id_created_by_trailblazer)
        + ',"logged_at":"2025-05-21","started_at":"2025-05-21",'
        '"completed_at":"","out_dir":"/out/dir","config_path":"/config/path"}'
    )

    mocker.patch.object(APIRequest, "api_request_from_content", return_value=successful_response)

    fake_trailblazer_host = "http://localhost/fake_trailblazer"

    trailblazer_api = TrailblazerAPI(
        config={
            "trailblazer": {
                "service_account": service_account,
                "service_account_auth_file": "/some/file",
                "host": fake_trailblazer_host,
            }
        }
    )

    case_id = "some_case_id"
    config_path = "/config/path"
    out_dir = "/out/dir"
    email = "noreply@scilifelab.se"
    order_id = 5
    tower_workflow_id = "some_workflow_id"
    ticket = "some_ticket"

    trailblazer_analysis: TrailblazerAnalysis = trailblazer_api.add_pending_analysis(
        case_id=case_id,
        workflow=Workflow.BALSAMIC,
        analysis_type=AnalysisType.OTHER,
        config_path=config_path,
        out_dir=out_dir,
        priority=TrailblazerPriority.LOW,
        email=email,
        order_id=order_id,
        ticket="some_ticket",
        tower_workflow_id=tower_workflow_id,
    )

    APIRequest.api_request_from_content.assert_called_with(
        api_method=APIMethods.POST,
        headers={"Authorization": f"Bearer {credentials.token}"},
        json={
            "case_id": case_id,
            "config_path": config_path,
            "out_dir": out_dir,
            "email": email,
            "workflow": "BALSAMIC",
            "order_id": order_id,
            "ticket": ticket,
            "is_hidden": False,
            "priority": TrailblazerPriority.LOW,
            "tower_workflow_id": tower_workflow_id,
            "type": AnalysisType.OTHER,
            "workflow_manager": WorkflowManager.Slurm,
        },
        url=f"{fake_trailblazer_host}/add-pending-analysis",
    )

    assert trailblazer_analysis.id == id_created_by_trailblazer
