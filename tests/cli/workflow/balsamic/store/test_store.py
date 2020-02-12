# """Tests for cg.cli.store.balsamic"""
# import logging
# from datetime import datetime
#
from cg.cli.workflow.balsamic.store import analysis

# from click import Path
#
EXIT_SUCCESS = 0


def test_store_analysis(cli_runner, balsamic_store_context, balsamic_case, meta_file):
    """Test store command without arguments"""

    # GIVEN a meta file for a balsamic analysis

    # WHEN calling store with meta file
    result = cli_runner.invoke(
        analysis, [balsamic_case.internal_id, meta_file], obj=balsamic_store_context
    )

    # THEN we should not get a message that the analysis has been stored
    assert result.exit_code == EXIT_SUCCESS
    assert "included files in Housekeeper" in result.output


def test_already_stored_analysis(
    cli_runner, balsamic_store_context, balsamic_case, meta_file
):
    """Test store command without arguments"""

    # GIVEN a meta file for a balsamic analysis
    # GIVEN the analysis has already been stored
    cli_runner.invoke(
        analysis, [balsamic_case.internal_id, meta_file], obj=balsamic_store_context
    )

    # WHEN calling store with meta file
    result = cli_runner.invoke(
        analysis, [balsamic_case.internal_id, meta_file], obj=balsamic_store_context
    )

    # THEN we should get a message that the analysis has previously been stored
    assert result.exit_code != EXIT_SUCCESS
    assert "analysis version already added" in result.output
