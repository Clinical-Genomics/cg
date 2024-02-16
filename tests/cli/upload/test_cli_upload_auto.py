"""Test the cli for uploading using auto"""

import datetime
import logging

from click.testing import CliRunner

from cg.cli.upload.base import upload_all_completed_analyses
from cg.constants import Workflow
from cg.models.cg_config import CGConfig
from tests.store_helpers import StoreHelpers


def test_upload_auto_with_workflow(
    cli_runner: CliRunner,
    helpers: StoreHelpers,
    timestamp: datetime.datetime,
    upload_context: CGConfig,
    caplog,
):
    """Test upload auto"""
    # GIVEN a store with a workflow
    workflow = Workflow.MIP_DNA
    helpers.add_analysis(store=upload_context.status_db, completed_at=timestamp, workflow=workflow)

    # WHEN uploading all analysis from workflow MIP
    caplog.set_level(logging.INFO)
    cli_runner.invoke(upload_all_completed_analyses, ["--workflow", "mip-dna"], obj=upload_context)
    # THEN assert that the MIP analysis was successfully uploaded
    assert "Uploading analysis for case" in caplog.text
