"""Tests for the compress fastq cli."""

import datetime as dt
import logging
from unittest.mock import Mock, call, create_autospec

from click.testing import CliRunner

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.compress.fastq import fastq_cmd, get_cases_to_process
from cg.cli.compress.helpers import (
    compress_fastq_to_spring_for_samples,
    get_samples_available_for_compression,
)
from cg.constants import Workflow
from cg.meta.compress import CompressAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers
from tests.typed_mock import TypedMock, create_typed_mock


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

    valid_compressable_case: Case = helpers.add_case(
        store=status_db,
        name=case_id,
        internal_id=case_id,
        data_analysis=Workflow.MIP_DNA,
        action=None,
    )
    valid_compressable_case.created_at = dt.datetime.now() - dt.timedelta(days=1000)
    status_db.session.commit()

    # WHEN running the compress command
    cases: list[Case] = get_cases_to_process(days_back=1, store=status_db)

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
    cases: list[Case] = get_cases_to_process(
        case_id=case_id_does_not_exist, days_back=1, store=status_db
    )

    # THEN assert no cases where found
    assert not cases

    # THEN assert we log no cases where found
    assert f"Could not find case {case_id_does_not_exist}" in caplog.text


def test_incompressible_cases_are_not_processable(
    helpers: StoreHelpers,
    populated_compress_context: CGConfig,
):
    """Test that cases that are marked as incompressible are not processable."""

    # GIVEN a store with a case that is marked as incompressible
    status_db: Store = populated_compress_context.status_db

    incompressible_case: Case = helpers.add_case(store=status_db, internal_id="incompressible")
    incompressible_case.created_at = dt.datetime.now() - dt.timedelta(days=1000)
    incompressible_case.is_compressible = False

    # WHEN retrieving the processable cases
    processable_cases: list[Case] = get_cases_to_process(days_back=1, store=status_db)

    # THEN assert that the incompressible case is not processable
    assert incompressible_case not in processable_cases


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
    populated_compress_context: CGConfig,
):
    """Test to run the compress command with a specified case id."""
    caplog.set_level(logging.DEBUG)
    status_db: Store = populated_compress_context.status_db

    # GIVEN a context with a case that can be compressed

    valid_compressable_case: Case = helpers.add_case(
        store=status_db,
        name=case_id,
        internal_id=case_id,
        data_analysis=Workflow.MIP_DNA,
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
    status_db.session.commit()

    # WHEN running the compress command
    res = cli_runner.invoke(fastq_cmd, ["--case-id", case_id], obj=populated_compress_context)

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0

    # THEN assert it was communicated that no families where found
    assert "individuals in 1 (completed) cases where compressed" in caplog.text


def test_compress_fastq_cli_multiple_family(
    caplog, cli_runner: CliRunner, populated_multiple_compress_context: CGConfig
):
    """Test to run the compress command with multiple families."""
    caplog.set_level(logging.DEBUG)
    # GIVEN a database with multiple families
    nr_cases = populated_multiple_compress_context.status_db._get_query(table=Case).count()
    assert nr_cases > 1

    # WHEN running the compress command
    res = cli_runner.invoke(
        fastq_cmd, ["--number-of-conversions", nr_cases], obj=populated_multiple_compress_context
    )

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0
    # THEN assert it was communicated that no families where found
    assert f"individuals in {nr_cases} (completed) cases where compressed" in caplog.text


def test_compress_fastq_cli_multiple_set_limit(
    caplog, cli_runner: CliRunner, populated_multiple_compress_context: CGConfig
):
    """Test to run the compress command with multiple families and use a limit."""
    compress_context = populated_multiple_compress_context
    caplog.set_level(logging.DEBUG)
    # GIVEN a context with more families than the limit
    nr_cases = compress_context.status_db._get_query(table=Case).count()
    limit = 5
    assert nr_cases > limit

    # WHEN running the compress command
    res = cli_runner.invoke(fastq_cmd, ["--number-of-conversions", limit], obj=compress_context)

    # THEN assert the program exits since no cases where found
    assert res.exit_code == 0
    # THEN assert it was communicated no more than the limited number of cases was compressed
    assert f"individuals in {limit} (completed) cases where compressed" in caplog.text


def test_get_samples_available_for_compression():
    # GIVEN list of sample ids
    samples: list[str] = ["sample1", "sample2"]

    # GIVEN a mocked housekeeper api
    housekeeper: TypedMock[HousekeeperAPI] = create_typed_mock(HousekeeperAPI)

    # GIVEN a housekeeper bundle with a file tagged with FASTQ
    housekeeper.as_type.get_bundle_names_with_fastq_files = Mock(return_value=samples)

    # GIVEN a store
    store: TypedMock[Store] = create_typed_mock(Store)

    # WHEN getting samples available for compression
    get_samples_available_for_compression(store=store.as_type, housekeeper=housekeeper.as_type)

    # THEN the correct calls was made
    housekeeper.as_mock.get_bundle_names_with_fastq_files.assert_called_once()
    store.as_mock.get_compressible_samples_by_internal_ids.assert_called_once_with(samples)


def test_get_samples_available_for_compression_input_case():
    # GIVEN list of sample ids
    samples: list[str] = ["sample1", "sample2"]

    # GIVEN a mocked housekeeper api
    housekeeper: HousekeeperAPI = create_autospec(HousekeeperAPI)

    # GIVEN a store
    store: TypedMock[Store] = create_typed_mock(Store)

    # GIVEN that a samples is linked to the input case
    store.as_type.get_sample_ids_by_case_id = Mock(return_value=samples)

    # WHEN getting samples available for compression with a case id
    get_samples_available_for_compression(
        store=store.as_type, housekeeper=housekeeper, case_id="case_id"
    )

    # THEN the correct calls was made
    store.as_mock.get_compressible_samples_by_internal_ids.assert_called_once_with(samples)


def test_get_samples_available_for_compression_missing_samples():
    # GIVEN a mocked housekeeper api
    housekeeper: TypedMock[HousekeeperAPI] = create_typed_mock(HousekeeperAPI)

    # GIVEN a housekeeper bundle with a file tagged with FASTQ
    housekeeper.as_type.get_bundle_names_with_fastq_files = Mock(return_value=[])

    # GIVEN a store
    store: TypedMock[Store] = create_typed_mock(Store)

    # WHEN getting samples available for compression
    get_samples_available_for_compression(store=store.as_type, housekeeper=housekeeper.as_type)

    # THEN the correct calls was made
    housekeeper.as_mock.get_bundle_names_with_fastq_files.assert_called_once()
    store.as_mock.get_compressible_samples_by_internal_ids.assert_not_called()


def test_get_samples_available_for_compression_input_case_missing_samples():
    # GIVEN a mocked housekeeper api
    housekeeper: HousekeeperAPI = create_autospec(HousekeeperAPI)

    # GIVEN a store
    store: TypedMock[Store] = create_typed_mock(Store)

    # GIVEN that no samples is linked to the input case
    store.as_type.get_sample_ids_by_case_id = Mock(return_value=[])

    # WHEN getting samples available for compression with a case id
    get_samples_available_for_compression(
        store=store.as_type, housekeeper=housekeeper, case_id="case_id"
    )

    # THEN the correct calls was made
    store.as_mock.get_compressible_samples_by_internal_ids.assert_not_called()


def test_compress_fastq_to_spring_for_samples():
    # GIVEN compress api
    compress_api: TypedMock[CompressAPI] = create_typed_mock(CompressAPI)

    # GIVEN a list of samples
    sample1: Sample = create_autospec(Sample, internal_id="sample1")
    sample2: Sample = create_autospec(Sample, internal_id="sample2")
    samples: list[Sample] = [sample1, sample2]

    # WHEN compressing samples
    compress_fastq_to_spring_for_samples(
        compress_api=compress_api.as_type,
        samples=samples,
        sample_limit=None,
    )

    # THEN correct method calls were made
    assert compress_api.as_mock.compress_fastq.call_args_list == [
        call(sample_id=sample1.internal_id),
        call(sample_id=sample2.internal_id),
    ]


def test_compress_fastq_to_spring_for_samples_with_limit():
    # GIVEN compress api
    compress_api: TypedMock[CompressAPI] = create_typed_mock(CompressAPI)

    # GIVEN a list of samples
    sample1: Sample = create_autospec(Sample, internal_id="sample1")
    sample2: Sample = create_autospec(Sample, internal_id="sample2")
    samples: list[Sample] = [sample1, sample2]

    # WHEN compressing samples with a sample limit of one
    compress_fastq_to_spring_for_samples(
        compress_api=compress_api.as_type,
        samples=samples,
        sample_limit=1,
    )

    # THEN only one call was made
    compress_api.as_mock.compress_fastq.assert_called_once_with(sample_id=sample1.internal_id)
