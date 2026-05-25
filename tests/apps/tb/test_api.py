import json
from datetime import datetime, timedelta, timezone
from unittest.mock import create_autospec

import pytest
from google.oauth2.service_account import IDTokenCredentials
from pytest_mock import MockerFixture
from requests import Response

from cg.apps.tb.api import TrailblazerAPI, requests
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
    credentials.expiry = datetime.now(timezone.utc) + timedelta(minutes=5)
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
            + ',"case_id": "case_id"'
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


def test_mark_analyses_as_delivered_success(
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a Trailblazer API
    tb_api = TrailblazerAPI(config=valid_trailblazer_config)

    response = Response()
    response.status_code = 200
    response._content = json.dumps({"key": "value"}).encode("utf-8")
    patch_call = mocker.patch.object(requests, "patch", return_value=response)

    # WHEN marking analyses as delivered
    tb_response: Response = tb_api.mark_analyses_as_delivered(
        signature="CG", trailblazer_ids=[1, 2, 3]
    )

    # THEN the expected request should have been sent
    expected_request = {
        "analyses": [
            {"id": 1, "is_delivered": True},
            {"id": 2, "is_delivered": True},
            {"id": 3, "is_delivered": True},
        ],
        "signature": "CG",
    }

    patch_call.assert_called_once_with(
        url=f"{tb_api.host}/analyses",
        headers={"Authorization": f"Bearer {valid_google_credentials.token}"},
        json=expected_request,
    )

    # THEN the response should be returned
    assert tb_response == response


def test_mark_analyses_as_delivered_with_forward_token(
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a Trailblazer API
    tb_api = TrailblazerAPI(config=valid_trailblazer_config)

    patch_call = mocker.patch.object(requests, "patch")

    # WHEN marking analyses as delivered
    tb_api.mark_analyses_as_delivered(
        auth_token="auth_token", signature=None, trailblazer_ids=[1, 2, 3]
    )

    # THEN the expected request should have been sent
    expected_request = {
        "analyses": [
            {"id": 1, "is_delivered": True},
            {"id": 2, "is_delivered": True},
            {"id": 3, "is_delivered": True},
        ],
        "signature": None,
    }

    patch_call.assert_called_once_with(
        url=f"{tb_api.host}/analyses",
        headers={
            "Authorization": f"Bearer {valid_google_credentials.token}",
            "X-On-Behalf-Of": "auth_token",
        },
        json=expected_request,
    )


def test_mark_analyses_as_delivered_fails_with_http_error(
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a Trailblazer API
    tb_api = TrailblazerAPI(config=valid_trailblazer_config)

    # GIVEN that the communication with Trailblazer fails
    mocker.patch.object(
        requests,
        "patch",
        return_value=create_autospec(
            requests.Response, ok=False, reason="I did not feel like it :("
        ),
    )

    # WHEN marking analyses as delivered
    # THEN a TrailblazerAPIHTTPError is raised
    with pytest.raises(TrailblazerAPIHTTPError):
        tb_api.mark_analyses_as_delivered(signature=None, trailblazer_ids=[1, 2, 3])


def test_get_analyses_to_deliver_for_case(
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a TrailblazerAPI
    tb_api = TrailblazerAPI(valid_trailblazer_config)

    # GIVEN that trailblazer returns an analysis
    mocker.patch.object(
        requests,
        "get",
        return_value=create_autospec(
            requests.Response,
            status_code=200,
            ok=True,
            text="{"
            '"analyses": ['
            "{"
            '"case_id": "case_1",'
            '"comment": null,'
            '"completed_at": null,'
            '"config_path": "/path/",'
            '"delivered_by": null,'
            '"delivered_date": null,'
            '"failed_job": null,'
            '"id": 1234,'
            '"is_cancellable": false,'
            '"is_delivered": false,'
            '"is_visible": true,'
            '"logged_at": "Sun, 10 May 2026 22:25:03 GMT",'
            '"order_id": 12345,'
            '"out_dir": "/some/path",'
            '"priority": "high",'
            '"progress": 0.0,'
            '"started_at": "Sun, 10 May 2026 22:25:03 GMT",'
            '"status": "pending",'
            '"ticket_id": "1234",'
            '"type": "other",'
            '"uploaded_at": null,'
            '"user_id": null,'
            '"version": null,'
            '"workflow": "raredisease",'
            '"workflow_manager": "slurm"'
            "}"
            "]}",
        ),
    )

    # WHEN getting analyses to deliver for case_1
    analyses = tb_api.get_analyses_to_deliver_for_case("case_1")

    # THEN the analysis should be returned
    assert analyses == [
        TrailblazerAnalysis(
            case_id="case_1",
            id=1234,
            logged_at="Sun, 10 May 2026 22:25:03 GMT",  # type: ignore pydantic
            started_at="Sun, 10 May 2026 22:25:03 GMT",  # type: ignore pydantic
            completed_at=None,
            out_dir="/some/path",  # type: ignore pydantic
            config_path="/path/",  # type: ignore pydantic
            status="pending",
            priority="high",
            is_visible=True,
            type="other",
            workflow=Workflow.RAREDISEASE,
        ),
    ]


def test_get_analyses_to_deliver_for_case_no_analysis(
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a trailblazer api
    tb_api = TrailblazerAPI(valid_trailblazer_config)

    # GIVEN that no analysis is to be delivered for a given case
    mocker.patch.object(
        requests,
        "get",
        return_value=create_autospec(
            requests.Response, status_code=200, ok=True, text='{"analyses":[],"total_count":0}'
        ),
    )

    # WHEN getting analyses to deliver
    analyses = tb_api.get_analyses_to_deliver_for_case("case_1")

    # THEN an empty list should be returned
    assert analyses == []


def test_get_analyses_to_deliver_for_case_improper_response(
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a trailblazer api
    tb_api = TrailblazerAPI(valid_trailblazer_config)

    # GIVEN an erroneous http response
    mocker.patch.object(
        requests,
        "get",
        return_value=create_autospec(
            requests.Response,
            status_code=500,
            ok=False,
        ),
    )

    # WHEN getting analyses to deliver
    # THEN a TrailblazerAPIHTTPError should be raised
    with pytest.raises(TrailblazerAPIHTTPError):
        tb_api.get_analyses_to_deliver_for_case("updog")


def test_get_all_analyses_to_deliver_success(
    response_with_one_rd_analysis_and_one_rsync_analysis: str,
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a TrailblazerAPI
    tb_api = TrailblazerAPI(valid_trailblazer_config)

    # GIVEN that trailblazer returns two analyses, one of which is an RSYNC analysis
    mocker.patch.object(
        requests,
        "get",
        return_value=create_autospec(
            requests.Response,
            status_code=200,
            ok=True,
            text=response_with_one_rd_analysis_and_one_rsync_analysis,
        ),
    )

    # WHEN getting all analyses to deliver
    analyses = tb_api.get_all_analyses_to_deliver()

    # THEN a list of one analysis is returned
    assert len(analyses) == 1

    # THEN the analysis' workflow is not DEMULTIPLEX nor RSYNC
    assert analyses[0].workflow not in [Workflow.DEMULTIPLEX, Workflow.RSYNC]


def test_get_all_analyses_to_deliver_improper_response(
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a TrailblazerAPI
    tb_api = TrailblazerAPI(valid_trailblazer_config)

    # GIVEN an erroneous http response
    mocker.patch.object(
        requests,
        "get",
        return_value=create_autospec(
            requests.Response,
            status_code=500,
            ok=False,
        ),
    )

    # WHEN getting analyses to deliver
    # THEN a TrailblazerAPIHTTPError should be raised
    with pytest.raises(TrailblazerAPIHTTPError):
        tb_api.get_all_analyses_to_deliver()
