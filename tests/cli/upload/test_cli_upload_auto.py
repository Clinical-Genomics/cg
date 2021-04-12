"""Test the cli for uploading using auto"""
import datetime
import logging

from cg.cli.upload.base import auto
from cg.constants import Pipeline
from cg.models.cg_config import CGConfig
from click.testing import CliRunner
from tests.store_helpers import StoreHelpers


def test_upload_auto_with_pipeline_as_argument(
    cli_runner: CliRunner,
    helpers: StoreHelpers,
    timestamp: datetime.datetime,
    upload_context: CGConfig,
    caplog,
):
    """Test upload auto"""
    # GIVEN a store with a MIP analysis
    pipeline = Pipeline.MIP_DNA
    helpers.add_analysis(store=upload_context.status_db, completed_at=timestamp, pipeline=pipeline)

    # WHEN uploading all analysis from pipeline MIP
    caplog.set_level(logging.INFO)
    cli_runner.invoke(auto, ["--pipeline", "mip-dna"], obj=upload_context)
    # THEN assert that the MIP analysis was successfully uploaded
    assert "Uploading family" in caplog.text
