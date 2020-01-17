""" This file groups all tests related to microsalt start creation """

import logging
from pathlib import Path
from snapshottest import Snapshot

from cg.cli.workflow.microsalt.base import start

EXIT_SUCCESS = 0


def test_no_arguments(cli_runner, base_context):
    """Test command without any options"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(start, obj=base_context)

    # THEN command should mention missing arguments
    assert result.exit_code != EXIT_SUCCESS


def test_dry_arguments(cli_runner, base_context, microbial_project_id, queries_path, caplog):
    """Test command dry """

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(start, ['--dry', microbial_project_id], obj=base_context)

    # THEN command should mention missing arguments
    assert result.exit_code == EXIT_SUCCESS

    outfilename = queries_path / microbial_project_id
    outfilename = outfilename.with_suffix(".json")
    assert f"/bin/true --parameters {outfilename}" in result.output

