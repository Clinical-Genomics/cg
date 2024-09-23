"""Test the cli for uploading using auto"""

import datetime
import logging
import pytest

from click.testing import CliRunner

from cg.cli.upload.base import upload_all_completed_analyses
from cg.constants import Workflow
from cg.models.cg_config import CGConfig
from tests.store_helpers import StoreHelpers

UPLOAD_CONTEXT_AND_WORKFLOWS = [
    ("balsamic", Workflow.BALSAMIC),
    ("microsalt", Workflow.MICROSALT),
    ("mip", Workflow.MIP_DNA),
    ("mip-rna", Workflow.MIP_RNA),
    ("raredisease", Workflow.RAREDISEASE),
    ("rnafusion", Workflow.RNAFUSION),
    ("taxprofiler", Workflow.TAXPROFILER),
    ("tomte", Workflow.TOMTE)]


@pytest.mark.parametrize(
    "upload_context, workflow",
    UPLOAD_CONTEXT_AND_WORKFLOWS,
    indirect=["upload_context"]
)
def test_upload_auto_with_workflow(
    cli_runner: CliRunner,
    workflow: Workflow,
    helpers: StoreHelpers,
    timestamp: datetime.datetime,
    upload_context: CGConfig,
    caplog,
):
    """Test upload auto: get analyses to upload, test upload completed."""
    # GIVEN a store with a workflow
    helpers.add_analysis(store=upload_context.status_db, completed_at=timestamp, workflow=workflow)

    # WHEN uploading all analyses
    caplog.set_level(logging.INFO)
    cli_runner.invoke(upload_all_completed_analyses, ["--workflow", workflow], obj=upload_context)
    # THEN assert that the MIP analysis was successfully uploaded
    assert "Uploading analysis for case" in caplog.text
