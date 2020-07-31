"""This script tests the cli method to clean old balsamic run dirs"""
from datetime import datetime, timedelta
from pathlib import Path
import logging

from cg.cli.clean import balsamic_past_run_dirs, balsamic_run_dir

EXIT_SUCCESS = 0


def test_past_run_dirs_without_options(cli_runner, clean_context):
    """Test command without options"""
    # GIVEN no case_id or options
    # WHEN dry running without anything specified
    result = cli_runner.invoke(balsamic_past_run_dirs, obj=clean_context)
    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_run_dir_without_options(cli_runner, clean_context):
    """Test command without options"""
    # GIVEN no case_id or options
    # WHEN dry running without anything specified
    result = cli_runner.invoke(balsamic_run_dir, obj=clean_context)
    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_with_yes(cli_runner, clean_context, helpers, caplog):
    """Test command with dry run options"""
    # GIVEN a case on disk that could be deleted
    timestamp_now = datetime.now()
    timestamp_yesterday = datetime.now() - timedelta(days=1)
    base_store = clean_context["BalsamicAnalysisAPI"].store
    analysis = helpers.add_analysis(
        base_store,
        pipeline="balsamic",
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
    )
    case_id = base_store.analyses_to_clean(pipeline="balsamic").first().family.internal_id
    case_path = clean_context["BalsamicAnalysisAPI"].get_case_path(case_id)
    Path(case_path).mkdir()

    # WHEN running with yes and remove stuff from before today
    result = cli_runner.invoke(
        balsamic_past_run_dirs, ["-y", str(timestamp_now)], obj=clean_context
    )

    # THEN the analysis should have been cleaned
    assert result.exit_code == EXIT_SUCCESS
    assert analysis.cleaned_at
    assert analysis not in base_store.analyses_to_clean(pipeline="balsamic")
    assert not Path(case_path).exists()


def test_dry_run(cli_runner, clean_context, helpers, caplog):
    """Test command with dry run options"""

    # GIVEN a case on disk that could be deleted
    caplog.set_level(logging.INFO)
    timestamp_yesterday = datetime.now() - timedelta(days=1)
    base_store = clean_context["BalsamicAnalysisAPI"].store
    helpers.add_analysis(
        base_store,
        pipeline="balsamic",
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
    )
    analysis_to_clean = base_store.analyses_to_clean(pipeline="Balsamic").first()
    case_id = analysis_to_clean.family.internal_id
    case_path = clean_context["BalsamicAnalysisAPI"].get_case_path(case_id)
    Path(case_path).mkdir()

    # WHEN dry running with dry run specified
    result = cli_runner.invoke(balsamic_run_dir, [case_id, "-d", "-y"], obj=clean_context)
    # THEN command should say it would have deleted
    assert result.exit_code == EXIT_SUCCESS

    with caplog.at_level(logging.INFO):
        assert "Would have deleted" in caplog.text
        assert case_id in caplog.text
    assert analysis_to_clean in base_store.analyses_to_clean(pipeline="Balsamic")


def test_cleaned_at(cli_runner, clean_context, helpers, caplog):
    """Test command with dry run options"""
    # GIVEN a case on disk that could be deleted
    timestamp_yesterday = datetime.now() - timedelta(days=1)
    base_store = clean_context["BalsamicAnalysisAPI"].store
    analysis = helpers.add_analysis(
        base_store,
        pipeline="balsamic",
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
    )
    case_id = base_store.analyses_to_clean(pipeline="balsamic")[0].family.internal_id
    case_path = clean_context["BalsamicAnalysisAPI"].get_case_path(case_id)
    Path(case_path).mkdir()
    # WHEN dry running with dry run specified
    result = cli_runner.invoke(balsamic_run_dir, [case_id, "-y"], obj=clean_context)

    # THEN command should say it would have deleted
    assert result.exit_code == EXIT_SUCCESS
    assert analysis.cleaned_at
    assert analysis not in base_store.analyses_to_clean(pipeline="Balsamic")
    assert not Path(case_path).exists()
