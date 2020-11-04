"""Tests for running the delivery command"""

import logging
from click.testing import CliRunner

from cg.cli.deliver.base import deliver_analysis
from cg.store import Store


def test_run_deliver_with_help(base_context: dict):
    # GIVEN a cli runner and a base context
    runner = CliRunner()

    # WHEN running the deliver command with help text
    result = runner.invoke(deliver_analysis, ["--help"], obj=base_context)

    # THEN assert the command exits without problems
    assert result.exit_code == 0
    # THEN assert that the help text is displayed
    assert "Deliver analysis files to customer inbox" in result.output


def test_run_deliver_without_specifying_case_or_ticket(base_context: dict, caplog):
    caplog.set_level(logging.INFO)
    # GIVEN a cli runner and a base context
    runner = CliRunner()

    # WHEN running the deliver command with help text
    result = runner.invoke(deliver_analysis, ["--delivery-type", "mip-dna"], obj=base_context)

    # THEN assert the command exits without problems
    assert result.exit_code == 0
    # THEN assert that the help text is displayed
    assert "Please provide a case-id or ticket-id" in result.output


def test_run_deliver_non_existing_case(base_context: dict, case_id: str, caplog):
    """Test to run the deliver command when the provided case does not exist"""
    caplog.set_level(logging.WARNING)
    # GIVEN a cli runner and a base context
    runner = CliRunner()
    # GIVEN a case_id that does not exist in the database
    store: Store = base_context["store"]
    assert store.family(case_id) is None

    # WHEN running the deliver command with the non existing case
    result = runner.invoke(
        deliver_analysis, ["--case-id", case_id, "--delivery-type", "mip-dna"], obj=base_context
    )

    # THEN assert the command exits without problems
    assert result.exit_code == 0
    # THEN assert that the correct warning is displayed
    assert f"Could not find case {case_id}" in caplog.text
