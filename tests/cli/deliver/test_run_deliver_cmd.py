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


def test_delivery_with_dry_run():
    """Test to run the delivery command with dry run enabled"""
    # GIVEN a context with a case that have files in housekeeper to deliver

    # WHEN running the deliver analysis command in dry run mode

    # THEN assert that the path to the delivery folder was not created

    # THEN assert that the correct information was communicateddsde++++++6
    assert 0


def test_delivery_path_created():
    """Test that the delivery path is created when running the deliver analysis command"""
    # GIVEN a context with a case that have files in housekeeper to deliver

    # GIVEN that the delivery file does not exist

    # WHEN running the deliver analysis command

    # THEN assert that the path to the delivery folder was created
    assert 0


def test_case_file_is_delivered():
    # GIVEN a context with a case that have files in housekeeper to deliver

    # WHEN running the deliver analysis command

    # THEN assert that the case file was delivered to the inbox
    assert 0
