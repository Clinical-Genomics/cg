"""Tests the CLI for generating delivery reports."""

import pytest
from _pytest.fixtures import FixtureRequest
from click.testing import Result, CliRunner

from cg.cli.generate.delivery_report.base import generate_delivery_report
from cg.constants import Workflow, EXIT_SUCCESS
from cg.models.cg_config import CGConfig


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_generate_delivery_report(
    request: FixtureRequest, workflow: Workflow, cli_runner: CliRunner
) -> None:
    """Test command to generate delivery report."""

    # GIVEN a delivery report context
    delivery_report_context: CGConfig = request.getfixturevalue(
        f"{workflow}_delivery_report_context"
    )

    # GIVEN a case ID
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")

    # WHEN calling delivery report generation
    result: Result = cli_runner.invoke(
        generate_delivery_report, [case_id], obj=delivery_report_context
    )

    # THEN the generation command should have successfully executed
    assert result.exit_code == EXIT_SUCCESS


@pytest.mark.parametrize("workflow", [Workflow.RAREDISEASE, Workflow.RNAFUSION])
def test_generate_delivery_report_dry_rum(
    request: FixtureRequest, workflow: Workflow, cli_runner: CliRunner
) -> None:
    """Test dry run command to generate delivery report."""

    # GIVEN a delivery report context
    delivery_report_context: CGConfig = request.getfixturevalue(
        f"{workflow}_delivery_report_context"
    )

    # GIVEN a case ID
    case_id: str = request.getfixturevalue(f"{workflow}_case_id")

    # WHEN calling delivery report generation with a dry option to print the HTML content to the terminal
    result: Result = cli_runner.invoke(
        generate_delivery_report, [case_id, "--dry-run"], obj=delivery_report_context
    )

    # THEN the generation command should have successfully executed
    assert result.exit_code == EXIT_SUCCESS
    assert "<!DOCTYPE html>" in result.output
