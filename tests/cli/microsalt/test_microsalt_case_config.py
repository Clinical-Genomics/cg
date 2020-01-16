""" This file groups all tests related to microsalt case config creation """

from pathlib import Path

import logging
from snapshottest import Snapshot

from cg.cli.microsalt import case_config

EXIT_SUCCESS = 0


def test_no_arguments(cli_runner, base_context, caplog):
    """Test command without any options"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(case_config, obj=base_context)

    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Aborted!" in result.output
    with caplog.at_level(logging.ERROR):
        assert "provide project and/or sample" in caplog.text


def test_dry_sample(cli_runner, base_context, microbial_sample_id, snapshot: Snapshot):
    """Test command without any options"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(case_config, ['--dry', microbial_sample_id], obj=base_context)

    # THEN command should mention argument
    assert result.exit_code == EXIT_SUCCESS
    snapshot.assert_match(result.output)
