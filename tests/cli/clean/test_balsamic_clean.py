"""This script tests the cli method to clean old balsamic run dirs"""

import datetime as dt
import logging
from pathlib import Path

from click.testing import CliRunner

from cg.apps.tb import TrailblazerAPI
from cg.cli.workflow.commands import clean_run_dir, past_run_dirs
from cg.constants import Workflow
from cg.models.cg_config import CGConfig
from tests.store_helpers import StoreHelpers

EXIT_SUCCESS = 0


def test_past_run_dirs_without_options(cli_runner: CliRunner, clean_context: CGConfig):
    """Test command without options"""
    # GIVEN no case_id or options
    # WHEN dry running without anything specified
    result = cli_runner.invoke(past_run_dirs, obj=clean_context)
    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_run_dir_without_options(cli_runner: CliRunner, clean_context: CGConfig):
    """Test command without options"""
    # GIVEN no case_id or options
    # WHEN dry running without anything specified
    result = cli_runner.invoke(clean_run_dir, obj=clean_context)
    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_with_yes(
    balsamic_case_clean: str,
    cli_runner: CliRunner,
    clean_context: CGConfig,
    timestamp_now: dt.datetime,
    helpers: StoreHelpers,
    caplog,
    mocker,
):
    """Test command with dry run options."""
    # GIVEN a case on disk that could be deleted
    analysis_api = clean_context.meta_apis["analysis_api"]

    analysis_to_clean = analysis_api.status_db.get_case_by_internal_id(
        balsamic_case_clean
    ).analyses[0]
    case_path = analysis_api.get_case_path(balsamic_case_clean)
    Path(case_path).mkdir(exist_ok=True, parents=True)

    mocker.patch.object(TrailblazerAPI, "is_latest_analysis_ongoing")
    TrailblazerAPI.is_latest_analysis_ongoing.return_value = False

    # WHEN running with yes and remove stuff from before today
    result = cli_runner.invoke(past_run_dirs, ["-y", str(timestamp_now)], obj=clean_context)
    # THEN the analysis should have been cleaned
    assert result.exit_code == EXIT_SUCCESS
    assert analysis_to_clean.cleaned_at
    assert analysis_to_clean not in analysis_api.get_analyses_to_clean(before=timestamp_now)
    assert not Path(case_path).exists()


def test_dry_run(
    balsamic_case_clean: str,
    cli_runner: CliRunner,
    clean_context: CGConfig,
    timestamp_yesterday: dt.datetime,
    helpers: StoreHelpers,
    caplog,
    mocker,
):
    """Test command with dry run options"""

    # GIVEN a case on disk that could be deleted
    caplog.set_level(logging.INFO)
    base_store = clean_context.status_db
    helpers.add_analysis(
        base_store,
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
        workflow=Workflow.BALSAMIC,
    )

    analysis_to_clean = base_store.get_case_by_internal_id(balsamic_case_clean).analyses[0]
    case_path = clean_context.meta_apis["analysis_api"].get_case_path(balsamic_case_clean)
    Path(case_path).mkdir(exist_ok=True, parents=True)

    mocker.patch.object(TrailblazerAPI, "is_latest_analysis_ongoing")
    TrailblazerAPI.is_latest_analysis_ongoing.return_value = False

    # WHEN dry running with dry run specified
    result = cli_runner.invoke(
        clean_run_dir, [balsamic_case_clean, "--dry-run", "-y"], obj=clean_context
    )
    # THEN command should say it would have deleted
    assert result.exit_code == EXIT_SUCCESS
    assert "Would have deleted" in caplog.text
    assert balsamic_case_clean in caplog.text
    assert analysis_to_clean in base_store.get_analyses_to_clean(workflow=Workflow.BALSAMIC)


def test_cleaned_at_valid(
    balsamic_case_clean: str, cli_runner: CliRunner, clean_context: CGConfig, caplog, mocker
):
    """Test command with dry run options"""
    # GIVEN a case on disk that could be deleted
    base_store = clean_context.status_db
    case_path = clean_context.meta_apis["analysis_api"].get_case_path(balsamic_case_clean)
    Path(case_path).mkdir(exist_ok=True, parents=True)

    mocker.patch.object(TrailblazerAPI, "is_latest_analysis_ongoing")
    TrailblazerAPI.is_latest_analysis_ongoing.return_value = False

    # WHEN dry running with dry run specified
    result = cli_runner.invoke(clean_run_dir, [balsamic_case_clean, "-y"], obj=clean_context)

    # THEN command should say it would have deleted
    assert result.exit_code == EXIT_SUCCESS
    assert base_store.get_case_by_internal_id("balsamic_case_clean").analyses[0].cleaned_at
    assert not Path(case_path).exists()


def test_cleaned_at_invalid(
    balsamic_case_not_clean: str, cli_runner: CliRunner, clean_context: CGConfig, caplog
):
    """Test command with dry run options"""
    # GIVEN a case on disk that could be deleted
    base_store = clean_context.status_db
    case_path = clean_context.meta_apis["analysis_api"].get_case_path(balsamic_case_not_clean)
    Path(case_path).mkdir(exist_ok=True, parents=True)
    assert not base_store.get_case_by_internal_id(balsamic_case_not_clean).analyses[0].cleaned_at
    # WHEN dry running with dry run specified

    result = cli_runner.invoke(past_run_dirs, ["2020-12-01", "--dry-run", "-y"], obj=clean_context)

    # THEN case directory should not have been cleaned
    assert result.exit_code == EXIT_SUCCESS
    assert not base_store.get_case_by_internal_id(balsamic_case_not_clean).analyses[0].cleaned_at
    assert Path(case_path).exists()
