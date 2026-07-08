import json
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, create_autospec

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


@pytest.fixture
def analysis_raw_response() -> str:
    return json.dumps(
        {
            "analyses": [
                {
                    "case_id": "case_1",
                    "comment": None,
                    "completed_at": None,
                    "config_path": "/path/",
                    "delivered_by": None,
                    "delivered_date": None,
                    "failed_job": None,
                    "id": 1234,
                    "is_cancellable": False,
                    "is_delivered": False,
                    "is_visible": True,
                    "logged_at": "Sun, 10 May 2026 22:25:03 GMT",
                    "order_id": 12345,
                    "out_dir": "/some/path",
                    "priority": "high",
                    "progress": 0.0,
                    "started_at": "Sun, 10 May 2026 22:25:03 GMT",
                    "status": "pending",
                    "ticket_id": "1234",
                    "type": "other",
                    "uploaded_at": None,
                    "user_id": None,
                    "version": None,
                    "workflow": "raredisease",
                    "workflow_manager": "slurm",
                }
            ]
        }
    )


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
        text=json.dumps(
            {
                "id": str(id_created_by_trailblazer),
                "case_id": "case_id",
                "logged_at": "2025-05-21",
                "started_at": "2025-05-21",
                "completed_at": "",
                "out_dir": "/out/dir",
                "config_path": "/config/path",
            }
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


@pytest.mark.parametrize("is_delivered", [True, False])
def test_set_analyses_delivery_status_success(
    is_delivered: bool,
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
    tb_response: Response = tb_api.set_analyses_delivery_status(
        is_delivered=is_delivered, signature="CG", trailblazer_ids=[1, 2, 3]
    )

    # THEN the expected request should have been sent
    expected_request = {
        "analyses": [
            {"id": 1, "is_delivered": is_delivered},
            {"id": 2, "is_delivered": is_delivered},
            {"id": 3, "is_delivered": is_delivered},
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


def test_set_analyses_delivery_status_with_forward_token(
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a Trailblazer API
    tb_api = TrailblazerAPI(config=valid_trailblazer_config)

    patch_call = mocker.patch.object(requests, "patch")

    # WHEN marking analyses as delivered
    tb_api.set_analyses_delivery_status(
        auth_token="auth_token", signature=None, trailblazer_ids=[1, 2, 3], is_delivered=True
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


def test_set_analyses_delivery_status_fails_with_http_error(
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
        tb_api.set_analyses_delivery_status(
            signature=None, trailblazer_ids=[1, 2, 3], is_delivered=True
        )


def test_get_analyses_to_deliver_for_case(
    analysis_raw_response: str,
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a TrailblazerAPI
    tb_api = TrailblazerAPI(valid_trailblazer_config)

    # GIVEN that Trailblazer returns an analysis
    request_mock = mocker.patch.object(
        requests,
        "get",
        return_value=create_autospec(
            requests.Response,
            status_code=200,
            ok=True,
            text=analysis_raw_response,
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

    # THEN the Trailblazer request should have been made with the expected parameters
    request_mock.assert_called_once_with(
        headers={"Authorization": "Bearer some_token"},
        json={},
        url="http://localhost/fake_trailblazer/analyses?case_id=case_1&status[]=completed&delivered=false&holdDelivery=false",
        verify=True,
    )


def test_get_analyses_to_deliver_for_case_no_analysis(
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a TrailblazerAPI
    tb_api = TrailblazerAPI(valid_trailblazer_config)

    # GIVEN that no analysis is to be delivered for a given case
    mocker.patch.object(
        requests,
        "get",
        return_value=create_autospec(
            requests.Response, status_code=200, ok=True, text='{"analyses":[],"total_count":0}'
        ),
    )

    # WHEN getting analyses to deliver for the given case
    analyses = tb_api.get_analyses_to_deliver_for_case("case_1")

    # THEN an empty list should be returned
    assert analyses == []


def test_get_analyses_to_deliver_for_case_improper_response(
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
        tb_api.get_analyses_to_deliver_for_case("updog")


def test_get_analyses_to_deliver_for_order(
    analysis_raw_response: str,
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a TrailblazerAPI
    tb_api = TrailblazerAPI(valid_trailblazer_config)

    # GIVEN that Trailblazer returns an analysis
    request_mock = mocker.patch.object(
        requests,
        "get",
        return_value=create_autospec(
            requests.Response,
            status_code=200,
            ok=True,
            text=analysis_raw_response,
        ),
    )

    # WHEN getting analyses to deliver for order 12345
    analyses = tb_api.get_analyses_to_deliver_for_order(12345)

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

    # THEN the Trailblazer request should have been made with the expected parameters
    request_mock.assert_called_once_with(
        headers={"Authorization": "Bearer some_token"},
        json={},
        url="http://localhost/fake_trailblazer/analyses?orderId=12345&status[]=completed&delivered=false&holdDelivery=false",
        verify=True,
    )


def test_get_analyses_to_deliver_for_order_no_analysis(
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a TrailblazerAPI
    tb_api = TrailblazerAPI(valid_trailblazer_config)

    # GIVEN that no analysis is to be delivered for a given order
    mocker.patch.object(
        requests,
        "get",
        return_value=create_autospec(
            requests.Response, status_code=200, ok=True, text='{"analyses":[],"total_count":0}'
        ),
    )

    # WHEN getting analyses to deliver for the given order
    analyses = tb_api.get_analyses_to_deliver_for_order(12345)

    # THEN an empty list should be returned
    assert analyses == []


def test_get_analyses_to_deliver_for_order_improper_response(
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

    # WHEN getting analyses to deliver for teh order
    # THEN a TrailblazerAPIHTTPError should be raised
    with pytest.raises(TrailblazerAPIHTTPError):
        tb_api.get_analyses_to_deliver_for_order(66666)


def test_get_all_completed_undelivered_analyses_success(
    response_with_two_analyses: str,
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a TrailblazerAPI
    tb_api = TrailblazerAPI(valid_trailblazer_config)

    # GIVEN that Trailblazer returns two analyses, one of which is an RSYNC analysis
    get_request = mocker.patch.object(
        requests,
        "get",
        return_value=create_autospec(
            requests.Response,
            status_code=200,
            ok=True,
            text=response_with_two_analyses,
        ),
    )

    # WHEN getting all analyses to deliver
    analyses = tb_api.get_all_analyses_to_deliver()

    # THEN a list of two analyses is returned
    assert len(analyses) == 2

    # THEN the correct url is called
    get_request.assert_called_once_with(
        headers={"Authorization": "Bearer some_token"},
        json={},
        url=f"{tb_api.host}/analyses?status[]=completed&delivered=false&holdDelivery=false",
        verify=True,
    )


def test_get_all_completed_undelivered_analyses_improper_response(
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a TrailblazerAPI
    tb_api = TrailblazerAPI(valid_trailblazer_config)

    # GIVEN an erroneous HTTP response
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


def test_get_all_completed_undelivered_analyses_exclude_workflow(
    response_with_two_analyses: str,
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a TrailblazerAPI
    tb_api = TrailblazerAPI(valid_trailblazer_config)

    # GIVEN that Trailblazer returns two analyses, one of which is an RSYNC analysis
    get_request = mocker.patch.object(
        requests,
        "get",
        return_value=create_autospec(
            requests.Response,
            status_code=200,
            ok=True,
            text=response_with_two_analyses,
        ),
    )

    # WHEN getting all analyses to deliver
    analyses = tb_api.get_all_analyses_to_deliver(
        exclude_workflows=[Workflow.RSYNC, Workflow.MIP_DNA]
    )

    # THEN a list of two analyses is returned
    assert len(analyses) == 2

    # THEN the correct url is called
    get_request.assert_called_once_with(
        headers={"Authorization": "Bearer some_token"},
        json={},
        url=f"{tb_api.host}/analyses?status[]=completed&delivered=false&holdDelivery=false&workflowExclude[]=RSYNC&workflowExclude[]=MIP-DNA",
        verify=True,
    )


def test_get_delivered_analyses_for_order_success(
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN a Successful HTTP called
    mocked_response = create_autospec(requests.Response, status_code=200, ok=True)
    mocked_response.json = Mock(
        return_value={
            "analyses": [
                {
                    "id": 1,
                    "case_id": "case_1",
                    "logged_at": "2025-05-21",
                    "started_at": "2025-05-21",
                    "completed_at": None,
                    "out_dir": "/path/to/out_dir",
                    "config_path": "/path/to/config",
                }
            ]
        }
    )
    http_call = mocker.patch.object(requests, "get", return_value=mocked_response)

    # GIVEN a TrailblazerAPI
    trailblazer_api = TrailblazerAPI(valid_trailblazer_config)

    # WHEN getting delivered analyses for an order
    trailblazer_api.get_delivered_analyses_for_order(order_id=12345)

    # THEN Trailblazer have been called with the correct parameters
    http_call.assert_called_once_with(
        url=f"{trailblazer_api.host}/analyses?orderId=12345&status[]=completed&delivered=true",
        headers=trailblazer_api.auth_header,
    )


def test_get_delivered_analyses_for_order_raises_error(
    valid_google_credentials: IDTokenCredentials,
    valid_trailblazer_config: dict,
    mocker: MockerFixture,
):
    # GIVEN an unsuccessful HTTP response
    mocker.patch.object(
        requests,
        "get",
        return_value=create_autospec(
            requests.Response,
            status_code=500,
            ok=False,
            reason="I did not feel like it :(",
        ),
    )

    # GIVEN a Trailblazer API
    trailblazer_api = TrailblazerAPI(valid_trailblazer_config)

    # WHEN getting delivered analyses for an order
    # THEN a TrailblazerAPIHTTPError should be raised
    with pytest.raises(TrailblazerAPIHTTPError):
        trailblazer_api.get_delivered_analyses_for_order(order_id=1)
