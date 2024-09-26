"""Tests the cli for generating delivery reports."""

import logging
from datetime import datetime

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner, Result

from cg.cli.generate.report.base import generate_delivery_report
from cg.constants import EXIT_FAIL, EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_delivery_report_invalid_case(
    mip_dna_context: CGConfig, cli_runner: CliRunner, caplog: LogCaptureFixture
):
    """Tests the delivery report command for an invalid case."""
    caplog.set_level(logging.INFO)

    # GIVEN a MIP DNA context object

    # WHEN calling delivery_report with an invalid case name
    result: Result = cli_runner.invoke(
        generate_delivery_report, ["not a case"], obj=mip_dna_context
    )

    # THEN the command should fail due to an invalid case ID
    assert "Invalid case ID. Retrieving available cases." in caplog.text
    assert "There are no valid cases to perform delivery report actions" in result.output
    assert result.exit_code == EXIT_FAIL


def test_delivery_report_dry_run(
    mip_dna_context: CGConfig, cli_runner: CliRunner, case_id: str, caplog: LogCaptureFixture
):
    """Tests the delivery report command with a dry run option."""
    caplog.set_level(logging.INFO)

    # GIVEN a MIP DNA context object

    # WHEN calling delivery_report with a dry option
    result: Result = cli_runner.invoke(
        generate_delivery_report, [case_id, "--dry-run"], obj=mip_dna_context
    )

    # THEN the command should be invoked successfully
    assert "create_delivery_report" in caplog.text
    assert "create_delivery_report_file" not in caplog.text
    assert "case=" + case_id in caplog.text
    assert "analysis_date=" + str(datetime.now().date()) in caplog.text
    assert result.exit_code == EXIT_SUCCESS


def test_delivery_report(
    mip_dna_context: CGConfig, cli_runner: CliRunner, case_id: str, caplog: LogCaptureFixture
):
    """Tests the delivery report command expecting a rendered html file."""
    caplog.set_level(logging.INFO)

    # GIVEN a MIP DNA context object

    # WHEN calling delivery_report with a dry option
    result: Result = cli_runner.invoke(generate_delivery_report, [case_id], obj=mip_dna_context)

    # THEN the report html should have been created and added to HK
    assert "create_delivery_report_file" in caplog.text
    assert "add_delivery_report_to_hk" in caplog.text
    assert result.exit_code == EXIT_SUCCESS
