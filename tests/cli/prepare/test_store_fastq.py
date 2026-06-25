"""Tests for the compress fastq cli"""

import logging

from click.testing import CliRunner

from cg.cli.prepare.prepare import prepare_case
from cg.models.cg_config import CGConfig


def test_prepare_case_fastq_cli_no_family(
    compress_context: CGConfig, cli_runner: CliRunner, caplog
):
    """Test to run the prepare command without providing any case id"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context

    # WHEN running the store fastq command
    res = cli_runner.invoke(prepare_case, [], obj=compress_context)

    # THEN assert the program exits with 2 since no argument was provided
    assert res.exit_code == 2


def test_prepare_case_fastq_cli_non_existing_family(
    compress_context: CGConfig, cli_runner: CliRunner, caplog
):
    """Test to run the prepare command with a non-existing case"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context and a non existing case id
    case_id = "happychap"

    # WHEN running the store fastq command
    res = cli_runner.invoke(prepare_case, [case_id], obj=compress_context)

    # THEN assert the program exits without a problem
    assert res.exit_code == 0
    # THEN assert it was communicated that no families where found
    assert f"Could not find case {case_id}" in caplog.text
