"""Test the cli for uploading using auto"""

from datetime import datetime
from unittest.mock import call

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.cli.upload import base as upload_cli
from cg.cli.upload.base import upload_all_completed_analyses
from cg.constants import Workflow
from cg.models.cg_config import CGConfig
from tests.store_helpers import StoreHelpers

WORKFLOWS_TO_TEST: list = [
    Workflow.BALSAMIC,
    Workflow.MICROSALT,
    Workflow.MIP_DNA,
    Workflow.MIP_RNA,
    Workflow.NALLO,
    Workflow.RAREDISEASE,
    Workflow.RNAFUSION,
    Workflow.TAXPROFILER,
    Workflow.TOMTE,
]


@pytest.mark.parametrize(
    "workflow",
    WORKFLOWS_TO_TEST,
)
def test_upload_auto_with_workflow(
    cli_runner: CliRunner,
    helpers: StoreHelpers,
    mocker: MockerFixture,
    upload_context: CGConfig,
    workflow: Workflow,
):
    """Test upload auto: get analyses to upload, test upload completed."""
    # GIVEN a store with an analysis which has timestamps for completion
    analysis = helpers.add_analysis(
        store=upload_context.status_db,
        completed_at=datetime.now(),
        workflow=workflow,
        housekeeper_version_id=1234,
    )

    # WHEN uploading all analyses
    mock_upload = mocker.patch.object(upload_cli, "upload")
    cli_runner.invoke(upload_all_completed_analyses, ["--workflow", workflow], obj=upload_context)

    # THEN assert that the upload function was called for the case
    mock_upload.assert_any_call(case_id=analysis.case.internal_id)


@pytest.mark.parametrize(
    "workflow",
    WORKFLOWS_TO_TEST,
)
def test_upload_auto_with_workflow_ignores_started_uploads(
    cli_runner: CliRunner,
    helpers: StoreHelpers,
    mocker: MockerFixture,
    upload_context: CGConfig,
    workflow: Workflow,
):
    # GIVEN a store with an analysis which has timestamps for completion and upload start
    analysis = helpers.add_analysis(
        store=upload_context.status_db,
        completed_at=datetime.now(),
        uploading=True,
        upload_started=datetime.now(),
        workflow=workflow,
        housekeeper_version_id=1234,
    )

    # WHEN uploading all analyses
    mock_upload = mocker.patch.object(upload_cli, "upload")
    cli_runner.invoke(upload_all_completed_analyses, ["--workflow", workflow], obj=upload_context)

    # THEN assert that the upload function was not called for the case
    assert call(case_id=analysis.case.internal_id) not in mock_upload.call_args_list
