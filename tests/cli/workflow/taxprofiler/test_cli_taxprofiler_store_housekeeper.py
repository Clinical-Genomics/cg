import logging
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner
from pydantic import ValidationError

from cg.cli.workflow.taxprofiler.base import store_housekeeper
from cg.constants import EXIT_SUCCESS
from cg.constants.constants import FileFormat
from cg.io.controller import WriteStream
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.utils import Process


def test_case_not_finished(
    cli_runner: CliRunner,
    taxprofiler_context: CGConfig,
    caplog: LogCaptureFixture,
    taxprofiler_case_id: str,
):
    """Test command with case_id and config file but no analysis_finish."""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id: str = taxprofiler_case_id

    # WHEN running
    result = cli_runner.invoke(store_housekeeper, [case_id], obj=taxprofiler_context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN warning should be printed that no deliverables file has been found
    assert "No deliverables file found for case" in caplog.text


