"""Tests for the compress fastq cli"""

import logging

from cg.cli.store import fastq_cmd


def test_store_fastq_cli_no_family(compress_context, cli_runner, caplog):
    """Test to run the compress command without providing any case id"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context

    # WHEN running the store fastq command
    res = cli_runner.invoke(fastq_cmd, [], obj=compress_context)

    # THEN assert the program exits with 2 since no argument was provided
    assert res.exit_code == 2


def test_store_fastq_cli_non_existing_family(compress_context, cli_runner, caplog):
    """Test to run the compress command witha non existing case"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context and a non existing case id
    case_id = "happychap"

    # WHEN running the store fastq command
    res = cli_runner.invoke(fastq_cmd, [case_id], obj=compress_context)

    # THEN assert the program exits without a problem
    assert res.exit_code == 0
    # THEN assert it was communicated that no families where found
    assert "Stored fastq files for 0 individuals" in caplog.text
