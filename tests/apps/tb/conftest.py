import json

import pytest


@pytest.fixture
def response_with_two_analyses() -> str:

    response_dict = {
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
                "workflow": "RAREDISEASE",
                "workflow_manager": "slurm",
            },
            {
                "case_id": "case_2",
                "comment": None,
                "completed_at": None,
                "config_path": "/path/",
                "delivered_by": None,
                "delivered_date": None,
                "failed_job": None,
                "id": 5678,
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
                "workflow": "RSYNC",
                "workflow_manager": "slurm",
            },
        ]
    }

    return json.dumps(response_dict)
