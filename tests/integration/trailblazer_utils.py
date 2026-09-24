"""Functions that mock responses from the Trailblazer REST API."""

from datetime import datetime
from pathlib import Path

from pytest_httpserver import HTTPServer
from werkzeug.datastructures import MultiDict

from cg.apps.environ import environ_email
from cg.constants import Workflow
from cg.constants.tb import AnalysisStatus, AnalysisType
from cg.store.models import Case


def expect_to_get_latest_analysis_with_empty_response(trailblazer_server: HTTPServer, case_id: str):
    trailblazer_server.expect_request(
        "/trailblazer/get-latest-analysis", data='{"case_id": "' + case_id + '"}'
    ).respond_with_json(None)


def expect_to_add_pending_analysis(
    trailblazer_server: HTTPServer,
    case: Case,
    ticket_id: int,
    out_dir: Path,
    config_path: Path | None,
    analysis_type: AnalysisType,
    workflow: Workflow,
    tower_workflow_id: str | None = None,
    workflow_manager: str = "slurm",
):
    """Mock the response from Trailblazer for TrailblazerAPI.add_pending_analysis.

    Mirrors cg.apps.tb.api.TrailblazerAPI.add_pending_analysis, which issues a POST
    to "{host}/add-pending-analysis" with a JSON body containing case, workflow,
    ticket, output, and optional config/tower workflow fields.
    """
    trailblazer_server.expect_request(
        "/trailblazer/add-pending-analysis",
        data=b'{"case_id": "%(case_id)s", "email": "%(email)s", "type": "%(type)s", '
        b'"config_path": %(config_path)s,'
        b' "order_id": 1, "out_dir": "%(out_dir)s", '
        b'"priority": "normal", "workflow": "%(workflow)s", "ticket": "%(ticket_id)s", '
        b'"workflow_manager": "%(workflow_manager)s", "tower_workflow_id": %(tower_workflow_id)s, "is_hidden": true}'
        % {
            b"email": environ_email().encode(),
            b"type": str(analysis_type).encode(),
            b"case_id": case.internal_id.encode(),
            b"ticket_id": str(ticket_id).encode(),
            b"tower_workflow_id": _quoted_string_or_null(tower_workflow_id),
            b"out_dir": str(out_dir).encode(),
            b"config_path": _quoted_string_or_null(config_path),
            b"workflow": str(workflow).upper().encode(),
            b"workflow_manager": str(workflow_manager).encode(),
        },
        method="POST",
    ).respond_with_json(
        {
            "id": "1",
            "case_id": "case_id",
            "logged_at": "",
            "started_at": "",
            "completed_at": "",
            "out_dir": "out/dir",
            "config_path": "config/path",
        }
    )


def expect_to_get_all_analyses_to_deliver(
    trailblazer_server: HTTPServer,
    exclude_workflows: list[Workflow],
):
    """Mock the response from Trailblazer for TrailblazerAPI.get_all_analyses_to_deliver.

    Mirrors cg.apps.tb.api.TrailblazerAPI.get_all_analyses_to_deliver, which issues a GET
    to "{host}/analyses?status[]=completed&delivered=false&holdDelivery=false" and optionally
    includes one or more "excludeWorkflow[]" query parameters.
    """
    query: MultiDict[str, str] = MultiDict(  # Decodes the URL without percent-encoding problems
        [
            ("status[]", AnalysisStatus.COMPLETED),
            ("delivered", "false"),
            ("holdDelivery", "false"),
        ]
    )
    for workflow in exclude_workflows or []:
        query.add("excludeWorkflow[]", workflow.upper())
    trailblazer_server.expect_request(
        "/trailblazer/analyses",
        query_string=query,
        method="GET",
    ).respond_with_json(
        {
            "analyses": [
                {
                    "id": 101,
                    "case_id": "case_1",
                    "logged_at": None,
                    "started_at": datetime.now().isoformat(),
                    "completed_at": datetime.now().isoformat(),
                    "status": AnalysisStatus.COMPLETED,
                    "out_dir": "/out/dir/case_1",
                    "config_path": "/config/case_1.yaml",
                    "workflow": Workflow.RAREDISEASE,
                },
                {
                    "id": 102,
                    "case_id": "case_2",
                    "logged_at": None,
                    "started_at": datetime.now().isoformat(),
                    "completed_at": datetime.now().isoformat(),
                    "status": AnalysisStatus.COMPLETED,
                    "out_dir": "/out/dir/case_2",
                    "config_path": "/config/case_2.yaml",
                    "workflow": Workflow.RAREDISEASE,
                },
            ]
        }
    )


def expect_to_get_delivered_analyses_for_order(
    trailblazer_server: HTTPServer, order_id: int, case_ids: list[str]
):
    """Mock the response from Trailblazer for TrailblazerAPI.get_delivered_analyses_for_order.

    Mirrors cg.apps.tb.api.TrailblazerAPI.get_delivered_analyses_for_order, which issues a GET
    to "{host}/analyses?orderId=<order_id>&status[]=completed&delivered=true".
    """
    trailblazer_server.expect_request(
        "/trailblazer/analyses",
        query_string=MultiDict(  # Decodes the URL without percent-encoding problems
            [
                ("orderId", str(order_id)),
                ("status[]", AnalysisStatus.COMPLETED),
                ("delivered", "true"),
            ]
        ),
        method="GET",
    ).respond_with_json(
        {
            "analyses": [
                {
                    "id": index,
                    "case_id": case_id,
                    "logged_at": None,
                    "started_at": datetime.now().isoformat(),
                    "completed_at": datetime.now().isoformat(),
                    "status": AnalysisStatus.COMPLETED,
                    "out_dir": f"/out/dir/{case_id}",
                    "config_path": f"/config/{case_id}.yaml",
                    "workflow": Workflow.RAREDISEASE,
                }
                for index, case_id in enumerate(case_ids)
            ]
        }
    )


def expect_to_set_analyses_as_delivered(
    trailblazer_server: HTTPServer,
    analysis_ids: list[int],
    is_delivered: bool = True,
    signature: str | None = None,
):
    """Mock the response from Trailblazer for TrailblazerAPI.set_analyses_delivery_status.

    This mirrors the request made in cg.apps.tb.api.TrailblazerAPI.set_analyses_delivery_status,
    which issues a PATCH to "{host}/analyses" with a JSON body of the form:
    {"analyses": [{"id": <id>, "is_delivered": <bool>}, ...], "signature": <signature>}
    """
    trailblazer_server.expect_request(
        "/trailblazer/analyses",
        json={
            "analyses": [
                {"id": analysis_id, "is_delivered": is_delivered} for analysis_id in analysis_ids
            ],
            "signature": signature,
        },
        method="PATCH",
    ).respond_with_json({"key": "value"})


def _quoted_string_or_null(value: str | Path | None) -> bytes:
    return (f'"{value}"' if value else "null").encode()
