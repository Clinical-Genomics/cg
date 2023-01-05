from click.testing import CliRunner

from cg.cli.workflow.commands import (
    balsamic_past_run_dirs,
    fluffy_past_run_dirs,
    microsalt_past_run_dirs,
    mip_past_run_dirs,
    mutant_past_run_dirs,
    rnafusion_past_run_dirs,
)
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig


def test_cli_workflow_clean_balsamic(
    cli_runner: CliRunner,
    base_context: CGConfig,
    before_date: str,
):
    # GIVEN a before string

    # WHEN running command in dry-run
    result = cli_runner.invoke(balsamic_past_run_dirs, [before_date], obj=base_context)

    # THEN command should terminate successfully
    assert result.exit_code == EXIT_SUCCESS


def test_cli_workflow_clean_fluffy(
    cli_runner: CliRunner,
    base_context: CGConfig,
    before_date: str,
):
    # GIVEN a before string

    # WHEN running command in dry-run
    result = cli_runner.invoke(fluffy_past_run_dirs, [before_date], obj=base_context)

    # THEN command should terminate successfully
    assert result.exit_code == EXIT_SUCCESS


def test_cli_workflow_clean_mip(
    cli_runner: CliRunner,
    base_context: CGConfig,
    before_date: str,
):
    # GIVEN a before string

    # WHEN running command in dry-run
    result = cli_runner.invoke(mip_past_run_dirs, [before_date], obj=base_context)

    # THEN command should terminate successfully
    assert result.exit_code == EXIT_SUCCESS


def test_cli_workflow_clean_mutant(
    cli_runner: CliRunner,
    base_context: CGConfig,
    before_date: str,
):
    # GIVEN a before string

    # WHEN running command in dry-run
    result = cli_runner.invoke(mutant_past_run_dirs, [before_date], obj=base_context)

    # THEN command should terminate successfully
    assert result.exit_code == EXIT_SUCCESS


def test_cli_workflow_clean_rnafusion(
    cli_runner: CliRunner,
    base_context: CGConfig,
    before_date: str,
):

    # GIVEN a before string

    # WHEN running command in dry-run
    result = cli_runner.invoke(rnafusion_past_run_dirs, [before_date], obj=base_context)

    # THEN command should exit successfully
    assert result.exit_code == EXIT_SUCCESS


def test_cli_workflow_clean_microsalt(
    cli_runner: CliRunner,
    base_context: CGConfig,
    before_date: str,
):

    # Given a before string

    # WHEN running command in dry-run
    result = cli_runner.invoke(microsalt_past_run_dirs, [before_date], obj=base_context)

    # THEN command should terminate successfully
    assert result.exit_code == EXIT_SUCCESS
