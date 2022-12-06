"""Tests cli methods to create the case config for RNAfusion"""

import logging
from typing import List

from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.workflow.rnafusion.base import config_case
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)


def test_without_options(cli_runner: CliRunner, rnafusion_context: CGConfig):
    """Test command without case_id."""
    # GIVEN NO case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(config_case, obj=rnafusion_context)
    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_with_missing_case(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    not_existing_case_id: str,
):
    """Test command with invalid case to start with."""
    caplog.set_level(logging.ERROR)
    # GIVEN case_id not in database
    assert not rnafusion_context.status_db.family(not_existing_case_id)
    # WHEN running
    result = cli_runner.invoke(config_case, [not_existing_case_id], obj=rnafusion_context)
    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case_id
    assert "could not be found in StatusDB!" in caplog.text


def test_without_samples(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    no_sample_case_id: str,
):
    """Test command with case_id and no samples."""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id: str = no_sample_case_id
    # WHEN running config case
    result = cli_runner.invoke(config_case, [case_id], obj=rnafusion_context)
    # THEN command should print the rnafusion command-string
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no sample is found
    assert case_id in caplog.text
    assert "has no samples" in caplog.text


def test_strandedness(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
):
    """Test command with --strandedness option."""
    caplog.set_level(logging.INFO)
    # GIVEN a VALID case_id and genome_version
    case_id: str = rnafusion_case_id
    option_key: str = "--strandedness"
    option_values: List[str] = ["reverse", "forward", "unstranded"]
    # WHEN running with strandedness option specified
    for option_value in option_values:
        result = cli_runner.invoke(
            config_case,
            [case_id, option_key, option_value],
            obj=rnafusion_context,
        )
        # THEN command should be generated successfully
        assert result.exit_code == EXIT_SUCCESS
        # THEN dry-print should include the option key and value
        assert option_key.replace("--", "") in caplog.text
        assert option_value in caplog.text


def test_wrong_strandedness(
    cli_runner: CliRunner,
    rnafusion_context: CGConfig,
    caplog: LogCaptureFixture,
    rnafusion_case_id: str,
):
    """Test command with --strandedness option."""
    caplog.set_level(logging.INFO)
    # GIVEN a VALID case_id and genome_version
    case_id: str = rnafusion_case_id
    option_key: str = "--strandedness"
    option_value: str = "unknown"
    # WHEN running with strandedness option specified
    result = cli_runner.invoke(
        config_case,
        [case_id, option_key, option_value],
        obj=rnafusion_context,
    )
    # THEN command should fail
    assert result.exit_code != EXIT_SUCCESS
