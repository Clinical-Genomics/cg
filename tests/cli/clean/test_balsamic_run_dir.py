"""This script tests the cli methods to clean balsamic run for a case in cg"""
import logging
from datetime import datetime

from cg.cli.clean import balsamic_run_dir
from cg.store import Store

EXIT_SUCCESS = 0


def test_without_options(cli_runner, clean_context):
    """Test command without options"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(balsamic_run_dir, obj=clean_context)

    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def ensure_balsamic_analysis(store: Store, helpers):
    timestamp = datetime.now()
    return helpers.add_analysis(store, pipeline="Balsamic", started_at=timestamp,
                                uploaded_at=timestamp,
                                cleaned_at=None)


def ensure_balsamic_directory(tmpdir, case_id):
    tmpdir.join(case_id).mkdir()


def test_dry_run(cli_runner, clean_context, base_store, helpers, caplog, tmpdir):
    """Test command with dry run options"""

    # GIVEN a case on disk that could be deleted
    caplog.set_level(logging.INFO)
    ensure_balsamic_analysis(base_store, helpers)
    analysis_to_clean = base_store.analyses_to_clean(pipeline="Balsamic").first()
    case_id = analysis_to_clean.family.internal_id
    ensure_balsamic_directory(tmpdir, case_id)

    # WHEN dry running with dry run specified
    result = cli_runner.invoke(balsamic_run_dir, [case_id, '-d', '-y'], obj=clean_context)

    # THEN command should say it would have deleted
    assert result.exit_code == EXIT_SUCCESS

    with caplog.at_level(logging.INFO):
        assert "Would have deleted" in caplog.text
        assert case_id in caplog.text
    assert analysis_to_clean in base_store.analyses_to_clean(pipeline="Balsamic")


def test_cleaned_at(cli_runner, clean_context, base_store, helpers, caplog, tmpdir):
    """Test command with dry run options"""

    # GIVEN a case on disk that could be deleted
    analysis = ensure_balsamic_analysis(base_store, helpers)
    case_id = base_store.analyses_to_clean(pipeline="Balsamic").first().family.internal_id
    ensure_balsamic_directory(tmpdir, case_id)

    # WHEN dry running with dry run specified
    result = cli_runner.invoke(balsamic_run_dir, [case_id, '-y'], obj=clean_context)

    # THEN command should say it would have deleted
    assert result.exit_code == EXIT_SUCCESS
    assert analysis.cleaned_at
    assert analysis not in base_store.analyses_to_clean(pipeline="Balsamic")
