"""This script tests the cli methods to create the case config for balsamic"""
import logging
from pathlib import Path

import pytest

from cg.cli.workflow.balsamic.base import config_case
from tests.cli.workflow.balsamic.conftest import balsamic_context

EXIT_SUCCESS = 0

def test_without_options(cli_runner, balsamic_context):
    """Test command with dry option"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(config_case, obj=balsamic_context)

    # THEN command should mention argument
    assert result.exit_code != EXIT_SUCCESS
    assert "Missing argument" in result.output


def test_with_missing_case(cli_runner, balsamic_context, caplog):
    """Test command with case to start with"""

    # GIVEN case-id not in database
    case_id = "soberelephant"

    assert not balsamic_context["BalsamicAnalysisAPI"].store.family(case_id)
    caplog.set_level(logging.WARNING)

    # WHEN running
    result = cli_runner.invoke(config_case, [case_id], obj=balsamic_context)

    # THEN command should successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    with caplog.at_level(logging.WARNING):
        assert case_id in caplog.text



def test_dry(cli_runner, balsamic_context, caplog):
    """Test command with --dry option"""

    # GIVEN case-id
    case_id = "balsamic_case_wgs_paired"
    caplog.set_level(logging.INFO)

    # WHEN dry running with dry specified
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)
    # THEN command should print the balsamic command-string
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        assert "balsamic" in caplog.text
        assert case_id in caplog.text


@pytest.mark.parametrize("option_key", ["--quality-trim", "--adapter-trim", "--umi"])
def test_passed_option(cli_runner, balsamic_context, option_key, balsamic_case, caplog):
    """Test command with option"""

    # GIVEN case-id
    caplog.set_level(logging.INFO)
    case_id = balsamic_case.internal_id
    balsamic_key = option_key

    # WHEN dry running with option specified
    result = cli_runner.invoke(
        config_case, [case_id, "--dry-run", option_key], obj=balsamic_context
    )

    # THEN dry-print should include the the balsamic option key
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        assert balsamic_key in caplog.text


def test_target_bed(cli_runner, balsamic_context, balsamic_case, caplog):
    """Test command with --target-bed option"""

    # GIVEN case-id
    caplog.set_level(logging.INFO)
    case_id = balsamic_case.internal_id
    option_key = "--target-bed"
    option_value = "target_bed"
    balsamic_key = "-p"

    # WHEN dry running with option specified
    result = cli_runner.invoke(
        config_case, [case_id, "--dry-run", option_key, option_value], obj=balsamic_context,
    )

    # THEN dry-print should include the the option-value
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        assert balsamic_key in caplog.text
        assert option_value in caplog.text


def get_beds_path(balsamic_context) -> Path:
    """Gets the bed path from the balsamic config"""
    return Path(balsamic_context.get("bed_path"))


def test_target_bed_from_lims(
    cli_runner, balsamic_context, balsamic_case, lims_api, balsamic_store, caplog
):
    """Test command without --target-bed option"""

    # GIVEN case that bed-version set in lims with same version existing in status db
    caplog.set_level(logging.INFO)

    for link in balsamic_case.links:
        lims_capture_kit = lims_api.capture_kit(link.sample.internal_id)
        assert lims_capture_kit
        bed_version = balsamic_store.latest_bed_version(lims_capture_kit)
        assert bed_version
        assert bed_version.filename

    bed_key = "-p"
    bed_path = get_beds_path(balsamic_context) / bed_version.filename
    case_id = balsamic_case.internal_id

    # WHEN dry running
    result = cli_runner.invoke(config_case, [case_id, "--dry-run"], obj=balsamic_context)

    # THEN dry-print should include the bed_key and the bed_value including path
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        assert bed_key in caplog.text
        assert str(bed_path) in caplog.text


def test_umi_trim_length(cli_runner, balsamic_context, balsamic_case, caplog):
    """Test command with --umi-trim-length option"""

    # GIVEN case-id
    caplog.set_level(logging.INFO)
    case_id = balsamic_case.internal_id
    option_key = "--umi-trim-length"
    option_value = "5"
    balsamic_key = option_key

    # WHEN dry running with option specified
    result = cli_runner.invoke(
        config_case, [case_id, "--dry-run", option_key, option_value], obj=balsamic_context,
    )

    # THEN dry-print should include the the option-value
    assert result.exit_code == EXIT_SUCCESS
    with caplog.at_level(logging.INFO):
        assert balsamic_key in caplog.text
        assert option_value in caplog.text
