"""Tests for the compress fastq cli"""

import logging

from cg.cli.compress.fastq import (
    decompress_sample,
    decompress_flowcell,
    decompress_ticket,
    decompress_case,
)


def test_decompress_spring_cli_no_family(compress_context, case_id, cli_runner, caplog):
    """Test to run the decompress command when no families are found"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context without families

    # WHEN running the compress command
    res = cli_runner.invoke(decompress_case, ["nonexisting_case"], obj=compress_context)

    # THEN assert the program exits since no cases were found
    assert res.exit_code == 0
    # THEN assert it was communicated that no families where found
    assert "Could not find case" in caplog.text


def test_decompress_spring_cli_one_family(populated_compress_context, cli_runner, case_id, caplog):
    """Test to run the decompress command with one family"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with a family

    # WHEN running the compress command
    res = cli_runner.invoke(decompress_case, [case_id], obj=populated_compress_context)

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0
    # THEN assert it was communicated that no families where found
    assert f"Decompressed spring archives in 3 samples" in caplog.text
