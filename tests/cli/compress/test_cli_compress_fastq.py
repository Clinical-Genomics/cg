"""Tests for the compress fastq cli."""

import datetime as dt
import logging
from typing import List

from cg.cli.compress.fastq import fastq_cmd, get_cases_to_process
from cg.constants import Pipeline
from cg.models.cg_config import CGConfig
from click.testing import CliRunner
from cg.store import Store
from cg.store.models import Family

from tests.store_helpers import StoreHelpers

MOCK_SET_MEM_ACCORDING_TO_READS_PATH: str = "cg.cli.compress.helpers.set_memory_according_to_reads"


def test_get_cases_to_process(
    case_id: str,
    cli_runner: CliRunner,
    helpers: StoreHelpers,
    populated_compress_context: CGConfig,
):
    """Test get cases to process."""

    # GIVEN a populated store
    status_db: Store = populated_compress_context.status_db

    # GIVEN a context with a case that can be compressed

    valid_compressable_case: Family = helpers.add_case(
        store=status_db,
        name=case_id,
        internal_id=case_id,
        data_analysis=Pipeline.MIP_DNA,
        action=None,
    )
    valid_compressable_case.created_at = dt.datetime.now() - dt.timedelta(days=1000)
    status_db.commit()

    # WHEN running the compress command
    cases: List[Family] = get_cases_to_process(days_back=1, store=status_db)

    # THEN assert cases are returned
    assert cases

    # THEN assert correct case was returned
    assert cases[0].internal_id == case_id


def test_get_cases_to_process_when_no_case(
    case_id_does_not_exist: str,
    caplog,
    cli_runner: CliRunner,
    helpers: StoreHelpers,
    populated_compress_context: CGConfig,
):
    """Test get cases to proces when there are no cases to compress."""
    caplog.set_level(logging.DEBUG)
    status_db: Store = populated_compress_context.status_db

    # WHEN running the compress command
    cases: List[Family] = get_cases_to_process(
        case_id=case_id_does_not_exist, days_back=1, store=status_db
    )

    # THEN assert no cases where found
    assert not cases

    # THEN assert we log no cases where found
    assert f"Could not find case {case_id_does_not_exist}" in caplog.text


def test_compress_fastq_cli_no_family(compress_context: CGConfig, cli_runner: CliRunner, caplog):
    """Test to run the compress command with a database without samples,"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context without families

    # WHEN running the compress command
    res = cli_runner.invoke(fastq_cmd, [], obj=compress_context)

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0

    # THEN assert it was communicated that no families where found
    assert "No cases to compress" in caplog.text


def test_compress_fastq_cli_case_id_no_family(
    case_id_does_not_exist: str, compress_context: CGConfig, cli_runner: CliRunner, caplog
):
    """Test to run the compress command when no families are found."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a context without families

    # WHEN running the compress command
    res = cli_runner.invoke(fastq_cmd, ["--case-id", case_id_does_not_exist], obj=compress_context)

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0

    # THEN assert it was communicated that no families where found
    assert f"Could not find case {case_id_does_not_exist}" in caplog.text


def test_compress_fastq_cli_case_id(
    case_id: str,
    caplog,
    cli_runner: CliRunner,
    helpers: StoreHelpers,
    mocker,
    populated_compress_context: CGConfig,
):
    """Test to run the compress command with a specified case id."""
    caplog.set_level(logging.DEBUG)
    status_db: Store = populated_compress_context.status_db

    # GIVEN a context with a case that can be compressed

    valid_compressable_case: Family = helpers.add_case(
        store=status_db,
        name=case_id,
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

    # GIVEN no adjusting according to readsa
    mocker.patch(MOCK_SET_MEM_ACCORDING_TO_READS_PATH, return_value=None)

    # WHEN running the compress command
    res = cli_runner.invoke(fastq_cmd, ["--case-id", case_id], obj=populated_compress_context)

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0

    # THEN assert it was communicated that no families where found
    assert f"individuals in 1 (completed) cases where compressed" in caplog.text


def test_compress_fastq_cli_multiple_family(
    caplog, cli_runner: CliRunner, mocker, populated_multiple_compress_context: CGConfig
):
    """Test to run the compress command with multiple families."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a database with multiple families
    nr_cases = populated_multiple_compress_context.status_db.families().count()
    assert nr_cases > 1

    # GIVEN no adjusting according to readsa
    mocker.patch(MOCK_SET_MEM_ACCORDING_TO_READS_PATH, return_value=None)

    # WHEN running the compress command
    res = cli_runner.invoke(
        fastq_cmd, ["--number-of-conversions", nr_cases], obj=populated_multiple_compress_context
    )

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0
    # THEN assert it was communicated that no families where found
    assert f"individuals in {nr_cases} (completed) cases where compressed" in caplog.text


def test_compress_fastq_cli_multiple_set_limit(
    caplog, cli_runner: CliRunner, mocker, populated_multiple_compress_context: CGConfig
):
    """Test to run the compress command with multiple families and use a limit."""
    compress_context = populated_multiple_compress_context
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with more families than the limit
    nr_cases = compress_context.status_db.families().count()
    limit = 5
    assert nr_cases > limit

    # GIVEN no adjusting according to readsa
    mocker.patch(MOCK_SET_MEM_ACCORDING_TO_READS_PATH, return_value=None)

    # WHEN running the compress command
    res = cli_runner.invoke(fastq_cmd, ["--number-of-conversions", limit], obj=compress_context)

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0
    # THEN assert it was communicated no more than the limited number of cases was compressed
    assert f"individuals in {limit} (completed) cases where compressed" in caplog.text
