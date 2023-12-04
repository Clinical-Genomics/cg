"""Tests CLI common methods to create the case config for NF analyses."""

import logging

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.rnafusion.base import metrics_deliver
from cg.cli.workflow.taxprofiler.base import metrics_deliver
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "context",
    ["rnafusion_context", "taxprofiler_context"],
)
def test_metrics_deliver_without_options(cli_runner: CliRunner, context: CGConfig, request):
    """Test metrics-deliver for Taxprofiler and Rnafusion without options."""
    context = request.getfixturevalue(context)

    # WHEN dry running without anything specified
    result = cli_runner.invoke(metrics_deliver, obj=context)

    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN command should mention argument
    assert "Missing argument" in result.output
