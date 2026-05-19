import pytest


@pytest.fixture
def raw_response():
    return (
        "{"
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
        "},"
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
        "]}"
    )
