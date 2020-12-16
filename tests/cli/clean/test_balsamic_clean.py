"""This script tests the cli method to clean old balsamic run dirs"""
import datetime as dt
import logging
from datetime import datetime, timedelta
from pathlib import Path

from cg.cli.clean import balsamic_past_run_dirs, balsamic_run_dir
from cg.constants import Pipeline

EXIT_SUCCESS = 0


def test_past_run_dirs_without_options(cli_runner, clean_context: dict):
    """Test command without options"""
    # GIVEN no case_id or options
    # WHEN dry running without anything specified
    result = cli_runner.invoke(balsamic_past_run_dirs, obj=clean_context)
    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_run_dir_without_options(cli_runner, clean_context: dict):
    """Test command without options"""
    # GIVEN no case_id or options
    # WHEN dry running without anything specified
    result = cli_runner.invoke(balsamic_run_dir, obj=clean_context)
    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_with_yes(cli_runner, clean_context: dict, timestamp_today: dt.datetime, helpers, caplog):
    """Test command with dry run options"""
    # GIVEN a case on disk that could be deleted
    store = clean_context["BalsamicAnalysisAPI"].store
    timestamp_now = timestamp_today

    case_id = "balsamic_case_clean"
    analysis_to_clean = store.family(case_id).analyses[0]
    case_path = clean_context["BalsamicAnalysisAPI"].get_case_path(case_id)
    Path(case_path).mkdir()

    # WHEN running with yes and remove stuff from before today
    result = cli_runner.invoke(
        balsamic_past_run_dirs, ["-y", str(timestamp_now)], obj=clean_context
    )
    # THEN the analysis should have been cleaned
    assert result.exit_code == EXIT_SUCCESS
    assert analysis_to_clean.cleaned_at
    assert analysis_to_clean not in store.analyses_to_clean(pipeline=Pipeline.BALSAMIC)
    assert not Path(case_path).exists()


def test_dry_run(
    cli_runner, clean_context: dict, timestamp_yesterday: dt.datetime, helpers, caplog
):
    """Test command with dry run options"""

    # GIVEN a case on disk that could be deleted
    caplog.set_level(logging.INFO)
    base_store = clean_context["BalsamicAnalysisAPI"].store
    helpers.add_analysis(
        base_store,
        pipeline=Pipeline.BALSAMIC,
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
    )
    case_id = "balsamic_case_clean"
    analysis_to_clean = base_store.family(case_id).analyses[0]
    case_path = clean_context["BalsamicAnalysisAPI"].get_case_path(case_id)
    Path(case_path).mkdir()

    # WHEN dry running with dry run specified
    result = cli_runner.invoke(balsamic_run_dir, [case_id, "-d", "-y"], obj=clean_context)
    # THEN command should say it would have deleted
    assert result.exit_code == EXIT_SUCCESS
    assert "Would have deleted" in caplog.text
    assert case_id in caplog.text
    assert analysis_to_clean in base_store.analyses_to_clean(pipeline=Pipeline.BALSAMIC)


def test_cleaned_at_valid(cli_runner, clean_context: dict, caplog):
    """Test command with dry run options"""
    # GIVEN a case on disk that could be deleted
    base_store = clean_context["BalsamicAnalysisAPI"].store
    case_id = "balsamic_case_clean"
    case_path = clean_context["BalsamicAnalysisAPI"].get_case_path(case_id)
    Path(case_path).mkdir()
    # WHEN dry running with dry run specified
    result = cli_runner.invoke(balsamic_run_dir, [case_id, "-y"], obj=clean_context)

    # THEN command should say it would have deleted
    assert result.exit_code == EXIT_SUCCESS
    assert base_store.family("balsamic_case_clean").analyses[0].cleaned_at
    assert not Path(case_path).exists()


def test_cleaned_at_invalid(cli_runner, clean_context: dict, caplog):
    """Test command with dry run options"""
    # GIVEN a case on disk that could be deleted
    base_store = clean_context["BalsamicAnalysisAPI"].store
    case_id = "balsamic_case_not_clean"
    case_path = clean_context["BalsamicAnalysisAPI"].get_case_path(case_id)
    Path(case_path).mkdir()
    assert not base_store.family("balsamic_case_not_clean").analyses[0].cleaned_at
    # WHEN dry running with dry run specified

    result = cli_runner.invoke(
        balsamic_past_run_dirs, ["2020-12-01", "-d", "-y"], obj=clean_context
    )

    # THEN case directory should not have been cleaned
    assert result.exit_code == EXIT_SUCCESS
    assert not base_store.family("balsamic_case_not_clean").analyses[0].cleaned_at
    assert Path(case_path).exists()
