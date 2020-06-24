"""This script tests the cli method to clean old balsamic run dirs"""
from datetime import datetime, timedelta

from cg.cli.clean import balsamic_past_run_dirs

EXIT_SUCCESS = 0


def test_without_options(cli_runner, base_context):
    """Test command without options"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(balsamic_past_run_dirs, obj=base_context)

    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_with_yes(cli_runner, clean_context, base_store, helpers, caplog, tmpdir):
    """Test command with dry run options"""

    # GIVEN a case on disk that could be deleted
    timestamp_now = datetime.now()
    timestamp_yesterday = datetime.now() - timedelta(days=1)
    analysis = helpers.add_analysis(
        base_store,
        pipeline="Balsamic",
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
    )
    case_id = base_store.analyses_to_clean(pipeline="Balsamic").first().family.internal_id
    tmpdir.join(case_id).mkdir()

    # WHEN running with yes and remove stuff from before today
    result = cli_runner.invoke(
        balsamic_past_run_dirs, ["-y", str(timestamp_now)], obj=clean_context
    )

    # THEN the analysis should have been cleaned
    assert result.exit_code == EXIT_SUCCESS
    assert analysis.cleaned_at
    assert analysis not in base_store.analyses_to_clean(pipeline="Balsamic")
