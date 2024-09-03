"""Tests for running the delivery command"""

import logging
from pathlib import Path

from click.testing import CliRunner

from cg.cli.deliver.base import deliver_case, deliver_ticket
from cg.constants.process import EXIT_SUCCESS, EXIT_FAIL, EXIT_PARSE_ERROR
from cg.models.cg_config import CGConfig
from cg.store.store import Store


def test_run_deliver_with_help(cli_runner: CliRunner, base_context: CGConfig):
    # GIVEN a cli runner and a base context

    # WHEN running the deliver command with help text
    result = cli_runner.invoke(deliver_case, ["--help"], obj=base_context)

    # THEN assert the command exits without problems
    assert result.exit_code == 0


def test_run_deliver_without_specifying_case(cli_runner: CliRunner, base_context: CGConfig, caplog):
    caplog.set_level(logging.INFO)
    # GIVEN a cli runner and a base context
    # WHEN running the deliver command with help text
    result = cli_runner.invoke(deliver_case, obj=base_context)

    # THEN assert the command exits without problems
    assert result.exit_code == EXIT_PARSE_ERROR


def test_run_deliver_non_existing_case(
    cli_runner: CliRunner,
    cg_context: CGConfig,
    case_id: str,
):
    """Test to run the deliver command when the provided case does not exist"""
    # GIVEN a cli runner and a base context

    # GIVEN a case_id that does not exist in the database
    store: Store = cg_context.status_db
    assert store.get_case_by_internal_id(internal_id=case_id) is None

    # WHEN running the deliver command with the non existing case
    result = cli_runner.invoke(
        deliver_case,
        ["--case-id", case_id],
        obj=cg_context,
    )

    # THEN assert the command exits without problems
    assert result.exit_code == 0
