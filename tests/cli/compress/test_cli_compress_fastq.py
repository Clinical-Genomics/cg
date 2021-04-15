"""Tests for the compress fastq cli"""

import datetime as dt
import logging

from cg.cli.compress.fastq import fastq_cmd
from cg.constants import Pipeline
from cg.models.cg_config import CGConfig
from click.testing import CliRunner
from cg.store import Store

from tests.store_helpers import StoreHelpers


def test_compress_fastq_cli_no_family(compress_context: CGConfig, cli_runner: CliRunner, caplog):
    """Test to run the compress command with a database without samples"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context without families

    # WHEN running the compress command
    res = cli_runner.invoke(fastq_cmd, [], obj=compress_context)

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0
    # THEN assert it was communicated that no families where found
    assert "Individuals in 0 (completed) cases where compressed" in caplog.text


def test_compress_fastq_cli_case_id_no_family(
    compress_context: CGConfig, cli_runner: CliRunner, caplog
):
    """Test to run the compress command when no families are found"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context without families
    case_id = "notrealcase"
    # WHEN running the compress command
    res = cli_runner.invoke(fastq_cmd, ["--case-id", case_id], obj=compress_context)

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0
    # THEN assert it was communicated that no families where found
    assert f"Could not find case {case_id}" in caplog.text


def test_compress_fastq_cli_case_id(
    populated_compress_context: CGConfig, cli_runner: CliRunner, helpers: StoreHelpers, caplog
):
    """Test to run the compress command with a specified case id"""
    caplog.set_level(logging.DEBUG)
    status_db: Store = populated_compress_context.status_db

    # GIVEN a context with a case that can be compressed
    case_id = "chonkywombat"

    valid_compressable_case = helpers.add_case(
        store=status_db,
        case_id=case_id,
        internal_id=case_id,
        data_analysis=Pipeline.MIP_DNA,
        action=None,
    )
    valid_compressable_case.created_at = dt.datetime.now() - dt.timedelta(days=1000)
    sample1 = helpers.add_sample(store=status_db, internal_id="ACCR9000")
    sample2 = helpers.add_sample(store=status_db, internal_id="ACCR9001")
    helpers.add_relationship(
        store=status_db,
        sample=sample1,
        case=valid_compressable_case,
    )
    helpers.add_relationship(
        store=status_db,
        sample=sample2,
        case=valid_compressable_case,
    )
    status_db.commit()

    # WHEN running the compress command
    res = cli_runner.invoke(fastq_cmd, ["--case-id", case_id], obj=populated_compress_context)

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0
    # THEN assert it was communicated that no families where found
    assert f"Individuals in 1 (completed) cases where compressed" in caplog.text


def test_compress_fastq_cli_multiple_family(
    populated_multiple_compress_context: CGConfig, cli_runner: CliRunner, caplog
):
    """Test to run the compress command with multiple families"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a database with multiple families
    nr_cases = populated_multiple_compress_context.status_db.families().count()
    assert nr_cases > 1

    # WHEN running the compress command
    res = cli_runner.invoke(
        fastq_cmd, ["--number-of-conversions", nr_cases], obj=populated_multiple_compress_context
    )

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0
    # THEN assert it was communicated that no families where found
    assert f"Individuals in {nr_cases} (completed) cases where compressed" in caplog.text


def test_compress_fastq_cli_multiple_set_limit(
    populated_multiple_compress_context: CGConfig, cli_runner: CliRunner, caplog
):
    """Test to run the compress command with multiple families and use a limit"""
    compress_context = populated_multiple_compress_context
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with more families than the limit
    nr_cases = compress_context.status_db.families().count()
    limit = 5
    assert nr_cases > limit

    # WHEN running the compress command
    res = cli_runner.invoke(fastq_cmd, ["--number-of-conversions", limit], obj=compress_context)

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0
    # THEN assert it was communicated no more than the limited number of cases was compressed
    assert f"Individuals in {limit} (completed) cases where compressed" in caplog.text
