import random
from pathlib import Path

from cg.cli.workflow.fluffy.base import run
from cg.constants import EXIT_SUCCESS, EXIT_FAIL
from cg.meta.workflow.fluffy import FluffyAnalysisAPI


def test_cli_run_dry(cli_runner, fluffy_case_id_existing, fluffy_context, caplog):
    caplog.set_level("INFO")
    result = cli_runner.invoke(run, [fluffy_case_id_existing, "--dry-run"], obj=fluffy_context)
    assert result.exit_code == EXIT_SUCCESS
    assert "Running command" in caplog.text


def test_cli_run(cli_runner, fluffy_case_id_existing, fluffy_context, caplog):
    caplog.set_level("INFO")
    result = cli_runner.invoke(run, [fluffy_case_id_existing], obj=fluffy_context)
    assert result.exit_code == EXIT_SUCCESS
    assert "Running command" in caplog.text
    assert "Trailblazer" in caplog.text
