"""Tests for the report-deliver cli command"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

from _pytest.logging import LogCaptureFixture
from cgmodels.cg.constants import Pipeline
from click.testing import CliRunner

from cg.cli.upload.base import upload
from cg.cli.workflow.rnafusion.base import report_deliver
from cg.constants import EXIT_SUCCESS, DataDelivery
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from tests.store_helpers import StoreHelpers


def test_upload_rnafusion(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    helpers: StoreHelpers,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
    mock_analysis_finish,
):
    """Test that a case that is already uploading can be force restarted."""
    caplog.set_level(logging.INFO)

    # GIVEN an a case with an analysis
    status_db: Store = rnafusion_context.status_db
    case_enough_reads: models.Family = helpers.add_case(
        store=status_db,
        internal_id=rnafusion_case_id,
        name=rnafusion_case_id,
        data_analysis=Pipeline.RNAFUSION,
    )
    analysis: models.Analysis = helpers.add_analysis(
        store=status_db,
        case=case_enough_reads,
        pipeline=Pipeline.RNAFUSION,
        data_delivery=DataDelivery.SCOUT,
        completed_at=datetime.now(),
    )

    # WHEN ensuring case config and analysis_finish exist where they should be stored

    # WHEN trying to upload it again with the force restart flag
    result = cli_runner.invoke(upload, ["-f", rnafusion_case_id], obj=rnafusion_context)
    a = result.output
    # THEN it tries to restart the upload    assert "already started" not in result.output

    assert "already started" not in result.output
