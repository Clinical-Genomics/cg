"""Tests CLI common methods to create the case config for NF analyses."""

import logging

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.rnafusion.base import metrics_deliver
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

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN command log should inform about missing arguments
    assert "Missing argument" in result.output


@pytest.mark.parametrize(
    "context",
    ["rnafusion_context", "taxprofiler_context"],
)
def test_metrics_deliver_with_missing_case(
    cli_runner: CliRunner,
    caplog: LogCaptureFixture,
    case_id_does_not_exist: str,
    context: CGConfig,
    request,
):
    """Test metrics-deliver for Taxprofiler and Rnafusion with a missing case."""
    caplog.set_level(logging.ERROR)
    context = request.getfixturevalue(context)

    # GIVEN a case not in the StatusDB database
    assert not context.status_db.get_case_by_internal_id(internal_id=case_id_does_not_exist)

    # WHEN running
    result = cli_runner.invoke(metrics_deliver, [case_id_does_not_exist], obj=context)

    # THEN command should not exit successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN ERROR log should be printed containing invalid case_id
    assert case_id_does_not_exist in caplog.text
    assert "could not be found" in caplog.text
