"""This script tests the cli methods to create the config for a balsamic config"""
import logging
import pytest
from cg.cli.balsamic import config

EXIT_SUCCESS = 0


def test_without_options(cli_runner, base_context):
    """Test command with dry option"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(config, obj=base_context)

    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_with_missing_case(cli_runner, base_context, caplog):
    """Test command with case to start with"""

    # GIVEN case-id not in database
    case_id = 'soberelephant'

    # WHEN running
    result = cli_runner.invoke(config, [case_id], obj=base_context)

    # THEN command should successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS

    with caplog.at_level(logging.ERROR):
        assert case_id in caplog.text



def test_dry(cli_runner, base_context, balsamic_case):
    """Test command with --dry option"""

    # GIVEN case-id
    case_id = balsamic_case.internal_id

    # WHEN dry running with dry specified
    result = cli_runner.invoke(config, [case_id, '--dry-run'], obj=base_context)
    
    # THEN command should print the balsamic command-string
    assert result.exit_code == EXIT_SUCCESS
    assert "balsamic" in result.output
    assert case_id in result.output


@pytest.mark.parametrize('option_key', [
    '--quality-trim',
    '--adapter-trim',
    '--umi',
])
def test_passed_option(cli_runner, base_context, option_key, balsamic_case):
    """Test command with option"""

    # GIVEN case-id
    case_id = balsamic_case.internal_id
    balsamic_key = option_key

    # WHEN dry running with option specified
    result = cli_runner.invoke(config, [case_id, '--dry-run', option_key], obj=base_context)


    # THEN dry-print should include the the balsamic option key
    assert result.exit_code == EXIT_SUCCESS
    assert balsamic_key in result.output


def test_target_bed(cli_runner, base_context, balsamic_case):
    """Test command with --target-bed option"""

    # GIVEN case-id
    case_id = balsamic_case.internal_id
    option_key = '--target-bed'
    option_value = 'target_bed'
    balsamic_key = '-p'

    # WHEN dry running with option specified
    result = cli_runner.invoke(config, [case_id, '--dry-run', option_key, option_value],
                               obj=base_context)

    # THEN dry-print should include the the option-value
    assert result.exit_code == EXIT_SUCCESS
    assert balsamic_key in result.output
    assert option_value in result.output


def test_umi_trim_length(cli_runner, base_context, balsamic_case):
    """Test command with --umi-trim-length option"""

    # GIVEN case-id
    case_id = balsamic_case.internal_id
    option_key = '--umi-trim-length'
    option_value = '5'
    balsamic_key = option_key

    # WHEN dry running with option specified
    result = cli_runner.invoke(config, [case_id, '--dry-run', option_key, option_value],
                               obj=base_context)

    # THEN dry-print should include the the option-value
    assert result.exit_code == EXIT_SUCCESS
    assert balsamic_key in result.output
    assert option_value in result.output
