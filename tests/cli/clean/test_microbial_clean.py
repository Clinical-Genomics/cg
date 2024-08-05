import datetime as dt
import logging
from pathlib import Path

from click.testing import CliRunner

from cg.apps.tb import TrailblazerAPI
from cg.cli.workflow.commands import clean_run_dir
from cg.constants import Workflow
from cg.models.cg_config import CGConfig
from tests.store_helpers import StoreHelpers

EXIT_SUCCESS = 0


def test_dry_run(
    microsalt_case_clean_dry: str,
    cli_runner: CliRunner,
    clean_context_microsalt: CGConfig,
    timestamp_yesterday: dt.datetime,
    helpers: StoreHelpers,
    caplog,
    mocker,
):
    """Test command with dry run options."""

    # GIVEN a case on disk that could be deleted
    caplog.set_level(logging.INFO)
    base_store = clean_context_microsalt.status_db
    helpers.add_analysis(
        base_store,
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
        workflow=Workflow.MICROSALT,
    )

    analysis_to_clean = base_store.get_case_by_internal_id(microsalt_case_clean_dry).analyses[0]
    case_path_list = clean_context_microsalt.meta_apis["analysis_api"].get_case_path(
        microsalt_case_clean_dry
    )

    for path in case_path_list:
        Path(path).mkdir(exist_ok=True, parents=True)

    mocker.patch.object(TrailblazerAPI, "is_latest_analysis_ongoing")
    TrailblazerAPI.is_latest_analysis_ongoing.return_value = False

    # WHEN dry running with dry run specified
    result = cli_runner.invoke(
        clean_run_dir, [microsalt_case_clean_dry, "--dry-run", "-y"], obj=clean_context_microsalt
    )

    # THEN command should say it would have deleted
    assert result.exit_code == EXIT_SUCCESS
    assert "Would have deleted" in caplog.text
    assert microsalt_case_clean_dry in caplog.text

    # THEN the analysis should still be in the analyses_to_clean query since this is a dry-ryn
    assert analysis_to_clean.cleaned_at == None
    assert analysis_to_clean in base_store.get_analyses_to_clean(workflow=Workflow.MICROSALT)


def test_clean_run(
    microsalt_case_clean: str,
    cli_runner: CliRunner,
    clean_context_microsalt: CGConfig,
    timestamp_yesterday: dt.datetime,
    helpers: StoreHelpers,
    caplog,
    mocker,
):
    """Test command with dry run options."""

    # GIVEN a case on disk that could be deleted
    caplog.set_level(logging.INFO)
    base_store = clean_context_microsalt.status_db
    helpers.add_analysis(
        base_store,
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
        workflow=Workflow.MICROSALT,
    )

    analysis_to_clean = base_store.get_case_by_internal_id(microsalt_case_clean).analyses[0]
    case_path_list = clean_context_microsalt.meta_apis["analysis_api"].get_case_path(
        microsalt_case_clean
    )

    for path in case_path_list:
        Path(path).mkdir(exist_ok=True, parents=True)

    mocker.patch.object(TrailblazerAPI, "is_latest_analysis_ongoing")
    TrailblazerAPI.is_latest_analysis_ongoing.return_value = False

    # WHEN dry running with dry run specified
    result = cli_runner.invoke(
        clean_run_dir, [microsalt_case_clean, "-y"], obj=clean_context_microsalt
    )

    # THEN command should say it would have deleted
    assert result.exit_code == EXIT_SUCCESS
    assert microsalt_case_clean in caplog.text
    assert "Cleaned" in caplog.text

    # THEN the analysis should no longer be in the analyses_to_clean query
    assert isinstance(analysis_to_clean.cleaned_at, dt.datetime)
    assert analysis_to_clean not in base_store.get_analyses_to_clean(workflow=Workflow.MICROSALT)
