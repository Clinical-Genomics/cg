"""Tests the cli for generating delivery reports"""

import logging
from datetime import datetime

from cg.cli.generate.commands import delivery_report
from cg.constants import EXIT_SUCCESS, EXIT_FAIL


def test_delivery_report_invalid_case(mip_dna_context, cli_runner, caplog):
    """Tests the delivery report command for an invalid case"""

    caplog.set_level(logging.INFO)

    # GIVEN a MIP DNA context object

    # WHEN calling delivery_report with an invalid case name
    result = cli_runner.invoke(
        delivery_report,
        ["not a case"],
        obj=mip_dna_context,
    )

    # THEN the command should fail due to an invalid case ID
    assert result.exit_code == EXIT_FAIL
    assert "Provide a case, suggestions:" in caplog.text


def test_delivery_report_dry_run(mip_dna_context, cli_runner, case_id, caplog):
    """Tests the delivery report command with a dry run option"""

    caplog.set_level(logging.INFO)

    # GIVEN a MIP DNA context object

    # WHEN calling delivery_report with a dry option
    result = cli_runner.invoke(
        delivery_report,
        [case_id, "--dry-run"],
        obj=mip_dna_context,
    )

    # THEN the command should be invoked successfully
    assert result.exit_code == EXIT_SUCCESS
    assert "create_delivery_report" in caplog.text
    assert "create_delivery_report_file" not in caplog.text
    assert "case=" + case_id in caplog.text
    assert "analysis_date=" + str(datetime.now().date()) in caplog.text


def test_delivery_report(mip_dna_context, cli_runner, case_id, caplog):
    """Tests the delivery report command expecting a rendered html file"""

    caplog.set_level(logging.INFO)

    # GIVEN a MIP DNA context object

    # WHEN calling delivery_report with a dry option
    result = cli_runner.invoke(
        delivery_report,
        [case_id],
        obj=mip_dna_context,
    )

    # THEN the call should be successful and the resultant delivery report file added to HK
    assert result.exit_code == EXIT_SUCCESS
    assert "create_delivery_report_file" in caplog.text
    assert "add_delivery_report_to_hk" in caplog.text
