from unittest.mock import create_autospec

import pytest
from google.oauth2.service_account import IDTokenCredentials
from requests import Response

from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants.constants import APIMethods, Workflow, WorkflowManager
from cg.constants.priority import TrailblazerPriority
from cg.constants.tb import AnalysisType
from cg.exc import TrailblazerAPIHTTPError
from cg.io.controller import APIRequest


@pytest.fixture
def valid_google_credentials(mocker) -> IDTokenCredentials:
    credentials: IDTokenCredentials = create_autospec(IDTokenCredentials)
    credentials.token = "some_token"
    mocker.patch.object(IDTokenCredentials, "from_service_account_file", return_value=credentials)
    return credentials


@pytest.fixture
def fake_trailblazer_host() -> str:
    return "http://localhost/fake_trailblazer"


@pytest.fixture
def valid_trailblazer_config(fake_trailblazer_host):
    return {
        "trailblazer": {
            "service_account": "service_account",
            "service_account_auth_file": "/some/file",
            "host": fake_trailblazer_host,
        }
    }


def test_add_pending_analysis_succeeds(
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    fake_trailblazer_host: str,
    mocker,
):
    # GIVEN there are valid credentials for calling Trailblazer
    # GIVEN a succesful response from Trailblazer
    id_created_by_trailblazer = 56

    successful_response: Response = create_autospec(
        Response,
        status_code=200,
        text=(
            '{"id":'
            + str(id_created_by_trailblazer)
            + ',"logged_at":"2025-05-21","started_at":"2025-05-21",'
            '"completed_at":"","out_dir":"/out/dir","config_path":"/config/path"}'
        ),
    )

    mocker.patch.object(APIRequest, "api_request_from_content", return_value=successful_response)

    # GIVEN a correctly configured TrailblazerAPI object
    trailblazer_api = TrailblazerAPI(config=valid_trailblazer_config)

    # GIVEN all neccessary values are provided
    case_id = "some_case_id"
    config_path = "/config/path"
    out_dir = "/out/dir"
    email = "noreply@scilifelab.se"
    order_id = 5
    tower_workflow_id = "some_workflow_id"
    ticket = "some_ticket"

    # WHEN add_pending_analysis is called
    trailblazer_analysis: TrailblazerAnalysis = trailblazer_api.add_pending_analysis(
        case_id=case_id,
        workflow=Workflow.BALSAMIC,
        analysis_type=AnalysisType.OTHER,
        config_path=config_path,
        out_dir=out_dir,
        priority=TrailblazerPriority.LOW,
        email=email,
        order_id=order_id,
        ticket=ticket,
        tower_workflow_id=tower_workflow_id,
    )

    # THEN a request with the correct parameters have been made to the Trailblazer API
    APIRequest.api_request_from_content.assert_called_with(
        api_method=APIMethods.POST,
        headers={"Authorization": f"Bearer {valid_google_credentials.token}"},
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

    # THEN the TrailblzerAnalysis object that was return includes the newly created id
    assert trailblazer_analysis.id == id_created_by_trailblazer


@pytest.mark.usefixtures("valid_google_credentials")
def test_add_pending_analysis_fails(valid_trailblazer_config: dict, mocker):
    # GIVEN there are valid credentials for calling Trailblazer
    # GIVEN an error response from Trailblazer
    error_response: Response = create_autospec(Response, ok=False, status_code=500)
    mocker.patch.object(APIRequest, "api_request_from_content", return_value=error_response)

    # GIVEN a correctly configured TrailblazerAPI object
    trailblazer_api = TrailblazerAPI(config=valid_trailblazer_config)

    # GIVEN all neccessary values are provided
    case_id = "some_case_id"
    config_path = "/config/path"
    out_dir = "/out/dir"
    email = "noreply@scilifelab.se"
    order_id = 5
    tower_workflow_id = "some_workflow_id"
    ticket = "some_ticket"

    # WHEN add_pending_analysis is called
    with pytest.raises(TrailblazerAPIHTTPError):
        # THEN a TrailblazerAPIHTTPError is raised
        trailblazer_api.add_pending_analysis(
            case_id=case_id,
            workflow=Workflow.BALSAMIC,
            analysis_type=AnalysisType.OTHER,
            config_path=config_path,
            out_dir=out_dir,
            priority=TrailblazerPriority.LOW,
            email=email,
            order_id=order_id,
            ticket=ticket,
            tower_workflow_id=tower_workflow_id,
        )
