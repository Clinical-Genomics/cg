"""Test the cli for uploading using auto"""
import logging

from cg.cli.upload.base import auto
from cg.constants import Pipeline


def test_upload_auto_with_pipeline_as_argument(
    cli_runner, caplog, helpers, timestamp, upload_context
):
    """Test upload auto"""
    # GIVEN a store with a MIP analysis
    pipeline = Pipeline.MIP_DNA
    analysis_api = upload_context["analysis_api"]
    helpers.add_analysis(store=analysis_api.status_db, completed_at=timestamp, pipeline=pipeline)

    # WHEN uploading all analysis from pipeline MIP
    caplog.set_level(logging.INFO)
    cli_runner.invoke(auto, ["--pipeline", "mip-dna"], obj=upload_context)
    # THEN assert that the MIP analysis was successfully uploaded
    assert "Uploading family" in caplog.text
