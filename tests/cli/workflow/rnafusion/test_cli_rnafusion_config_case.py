"""Tests cli methods to create the case config for balsamic"""

import logging

from cg.cli.workflow.rnafusion.base import config_case
from click.testing import CliRunner

from cg.models.cg_config import CGConfig

EXIT_SUCCESS = 0

LOG = logging.getLogger(__name__)


def test_without_options(cli_runner: CliRunner, rnafusion_context: CGConfig):
    """Test command without case_id"""
    # GIVEN NO case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(config_case, obj=rnafusion_context)
    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_with_missing_case(cli_runner: CliRunner, rnafusion_context: CGConfig, caplog):
    """Test command with invalid case to start with"""
    caplog.set_level(logging.ERROR)
    # GIVEN case_id not in database
    case_id = "soberelephant"
    assert not rnafusion_context.status_db.family(case_id)
    # WHEN running
    result = cli_runner.invoke(config_case, [case_id], obj=rnafusion_context)
    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case_id
    assert "could not be found in StatusDB!" in caplog.text


def test_without_samples(cli_runner: CliRunner, rnafusion_context: CGConfig, caplog):
    """Test command with case_id and no samples"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "no_sample_case"
    # WHEN running config case
    result = cli_runner.invoke(config_case, [case_id], obj=rnafusion_context)
    # THEN command should print the rnafusion command-string
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no sample is found
    assert case_id in caplog.text
    assert "has no samples" in caplog.text


def test_strandedness(cli_runner: CliRunner, rnafusion_context: CGConfig, caplog):
    """Test command with --strandedness option"""
    caplog.set_level(logging.INFO)
    # GIVEN a VALID case_id and genome_version
    case_id = "case_enough_reads"
    option_key = "--strandedness"
    option_values = ["reverse", "forward", "unstranded"]
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


def test_wrong_strandedness(cli_runner: CliRunner, rnafusion_context: CGConfig, caplog):
    """Test command with --strandedness option"""
    caplog.set_level(logging.INFO)
    # GIVEN a VALID case_id and genome_version
    case_id = "case_rnafusion_enough_reads"
    option_key = "--strandedness"
    option_value = "unknown"
    # WHEN running with strandedness option specified
    result = cli_runner.invoke(
        config_case,
        [case_id, option_key, option_value],
        obj=rnafusion_context,
    )
    # THEN command should fail
    assert result.exit_code != EXIT_SUCCESS
