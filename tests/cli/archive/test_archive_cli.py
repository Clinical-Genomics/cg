from click.testing import CliRunner

from cg.cli.archive import archive_spring_files
from cg.models.cg_config import CGConfig


def test_limit_and_archive_all_fails(cli_runner: CliRunner, cg_context: CGConfig):
    """Tests that when invoking archive-spring-files in the Archive CLI module, the command is aborted
    if both a limit and the --archive-all flag is provided."""

    # GIVEN a CLI runner and a context

    # WHEN invoking archive_spring_files with both a given limit and specifying archive_all
    result = cli_runner.invoke(
        archive_spring_files,
        ["--limit", 100, "--archive-all"],
        obj=cg_context,
    )

    # THEN the command should have exited with an exit_code 1
    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert (
        "Incorrect input parameters - please do not provide both a limit and set --archive-all."
        in result.stdout
    )
