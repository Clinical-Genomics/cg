from cg.cli.workflow.fluffy.base import run
from cg.constants import EXIT_SUCCESS


def test_cli_run_dry(cli_runner, fluffy_case_id_existing, fluffy_context, caplog):

    caplog.set_level("INFO")

    # GIVEN a case_id that does exist in database

    # WHEN running command in dry-run mode
    result = cli_runner.invoke(run, [fluffy_case_id_existing, "--dry-run"], obj=fluffy_context)

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN log informs about process running
    assert "Running command" in caplog.text


def test_cli_run_dry_no_case(
    cli_runner,
    fluffy_case_id_non_existing,
    fluffy_context,
    caplog,
):
    caplog.set_level("ERROR")

    # GIVEN a case_id that does NOT exist in database

    # WHEN running command in dry-run mode
    result = cli_runner.invoke(run, [fluffy_case_id_non_existing, "--dry-run"], obj=fluffy_context)

    # THEN command does not terminate successfully
    assert result.exit_code != EXIT_SUCCESS

    # THEN logging informs about the case_id not existing
    assert fluffy_case_id_non_existing in caplog.text
    assert "could not be found" in caplog.text


def test_cli_run(cli_runner, fluffy_case_id_existing, fluffy_context, caplog):

    caplog.set_level("INFO")

    # GIVEN a case_id that does exist in database

    # WHEN running command
    result = cli_runner.invoke(run, [fluffy_case_id_existing], obj=fluffy_context)

    # THEN command terminates successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN log informs about process running
    assert "Running command" in caplog.text

    # THEN log informs about the analysis being tracked in Trailblazer
    assert "Trailblazer" in caplog.text
