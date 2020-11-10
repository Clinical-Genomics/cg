"""Test the cli for uploading using auto"""
import logging

from cg.cli.upload.base import auto
from cg.constants import Pipeline


def test_upload_auto_with_pipeline_as_argument(
    base_context, cli_runner, caplog, helpers, sample_store, timestamp
):
    """Test upload auto"""
    # GIVEN a store with a MIP analysis
    pipeline = Pipeline.BALSAMIC
    helpers.add_analysis(store=sample_store, completed_at=timestamp, pipeline=pipeline)

    # WHEN uploading all analysis from pipeline MIP
    caplog.set_level(logging.INFO)
    cli_runner.invoke(
        auto, ["--pipeline", str(pipeline)], obj=base_context, catch_exceptions=False
    )

    # THEN assert that the MIP analysis was successfully uploaded
    with caplog.at_level(logging.INFO):
        assert "Uploading family" in caplog.text
