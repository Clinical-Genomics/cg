"""Tests for the compress fastq cli"""

import logging

from cg.cli.compress.fastq import fastq_cmd


def test_compress_fastq_cli_no_family(compress_context, cli_runner, caplog):
    """Test to run the compress command with a database without samples"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context without families

    # WHEN running the compress command
    res = cli_runner.invoke(fastq_cmd, [], obj=compress_context)

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0
    # THEN assert it was communicated that no families where found
    assert "Individuals in 0 (completed) cases where compressed" in caplog.text


def test_compress_fastq_cli_case_id_no_family(compress_context, cli_runner, case_id, caplog):
    """Test to run the compress command when no families are found"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context without families

    # WHEN running the compress command
    res = cli_runner.invoke(fastq_cmd, ["--case-id", case_id], obj=compress_context)

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0
    # THEN assert it was communicated that no families where found
    assert f"Could not find case {case_id}" in caplog.text


def test_real_compress_fastq_cli_one_family(
    real_populated_compress_context, cli_runner, case_id, caplog
):
    """Test to run the compress command there is an existing family"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with a family
    # WHEN running the compress command
    res = cli_runner.invoke(fastq_cmd, ["--case-id", case_id], obj=real_populated_compress_context)

    # THEN assert the program exits with a non zero exit status
    assert res.exit_code == 0
    # THEN assert it was communicated that one family was compressed
    assert f"Individuals in 1 (completed) cases where compressed" in caplog.text


def test_compress_fastq_cli_case_id(populated_compress_context, cli_runner, case_id, caplog):
    """Test to run the compress command with a specified case id"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with a family

    # WHEN running the compress command
    res = cli_runner.invoke(fastq_cmd, ["--case-id", case_id], obj=populated_compress_context)

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0
    # THEN assert it was communicated that no families where found
    assert f"Individuals in 1 (completed) cases where compressed" in caplog.text


def test_compress_fastq_cli_multiple_family(
    populated_multiple_compress_context, cli_runner, caplog
):
    """Test to run the compress command with multiple families"""
    compress_context = populated_multiple_compress_context
    caplog.set_level(logging.DEBUG)
    # GIVEN a database with multople families
    nr_cases = sum(1 for i in compress_context["status_db"].families())
    assert nr_cases > 1

    # WHEN running the compress command
    res = cli_runner.invoke(fastq_cmd, ["--number-of-conversions", nr_cases], obj=compress_context)

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0
    # THEN assert it was communicated that no families where found
    assert f"Individuals in {nr_cases} (completed) cases where compressed" in caplog.text


def test_compress_fastq_cli_multiple_set_limit(
    populated_multiple_compress_context, cli_runner, caplog
):
    """Test to run the compress command with multiple families and use a limit"""
    compress_context = populated_multiple_compress_context
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with more families than the limit
    nr_cases = sum(1 for i in compress_context["status_db"].families())
    limit = 5
    assert nr_cases > limit

    # WHEN running the compress command
    res = cli_runner.invoke(fastq_cmd, ["--number-of-conversions", limit], obj=compress_context)

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0
    # THEN assert it was communicated no more than the limited number of cases was compressed
    assert f"Individuals in {limit} (completed) cases where compressed" in caplog.text
