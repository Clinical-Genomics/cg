"""Tests for the compress fastq cli."""

import datetime as dt
import logging
from unittest.mock import Mock, call, create_autospec

from click.testing import CliRunner, Result
from pytest_mock import MockFixture

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.compress import fastq as fastq_module
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


def test_compress_fastq_cli(cli_runner: CliRunner, cg_context: CGConfig, mocker: MockFixture):
    # GIVEN a store, housekeeper api and compress api on the context
    store: Store = create_autospec(Store)
    housekeeper: HousekeeperAPI = create_autospec(HousekeeperAPI)
    compress_api: CompressAPI = create_autospec(CompressAPI)
    cg_context.status_db_ = store
    cg_context.housekeeper_api_ = housekeeper
    cg_context.meta_apis["compress_api"] = compress_api

    # GIVEN samples available for compression
    sample1: Sample = create_autospec(Sample, internal_id="sample1")
    sample2: Sample = create_autospec(Sample, internal_id="sample2")
    samples: list[Sample] = [sample1, sample2]
    get_samples_mock = mocker.patch.object(
        fastq_module, "get_samples_available_for_compression", return_value=samples
    )
    compress_samples_mock = mocker.patch.object(
        fastq_module, "compress_fastq_to_spring_for_samples"
    )

    # WHEN running the compress fastq command
    result: Result = cli_runner.invoke(fastq_cmd, [], obj=cg_context)

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN samples were fetched using the context's store and housekeeper api
    get_samples_mock.assert_called_once_with(store=store, housekeeper=housekeeper, case_id=None)

    # THEN the samples were sent for compression using the default limit
    compress_samples_mock.assert_called_once_with(
        compress_api=compress_api, samples=samples, sample_limit=5
    )


def test_compress_fastq_cli_no_samples(
    cli_runner: CliRunner, cg_context: CGConfig, mocker: MockFixture
):
    # GIVEN a store, housekeeper api and compress api on the context
    store: Store = create_autospec(Store)
    housekeeper: HousekeeperAPI = create_autospec(HousekeeperAPI)
    compress_api: CompressAPI = create_autospec(CompressAPI)
    cg_context.status_db_ = store
    cg_context.housekeeper_api_ = housekeeper
    cg_context.meta_apis["compress_api"] = compress_api

    # GIVEN no samples available for compression
    get_samples_mock = mocker.patch.object(
        fastq_module, "get_samples_available_for_compression", return_value=[]
    )
    compress_samples_mock = mocker.patch.object(
        fastq_module, "compress_fastq_to_spring_for_samples"
    )

    # WHEN running the compress fastq command
    result: Result = cli_runner.invoke(fastq_cmd, [], obj=cg_context)

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN samples were fetched using the context's store and housekeeper api
    get_samples_mock.assert_called_once_with(store=store, housekeeper=housekeeper, case_id=None)

    # THEN no samples were sent for compression
    compress_samples_mock.assert_not_called()


def test_compress_fastq_cli_case_id(
    cli_runner: CliRunner, cg_context: CGConfig, mocker: MockFixture
):
    # GIVEN a store, housekeeper api and compress api on the context
    store: Store = create_autospec(Store)
    housekeeper: HousekeeperAPI = create_autospec(HousekeeperAPI)
    compress_api: CompressAPI = create_autospec(CompressAPI)
    cg_context.status_db_ = store
    cg_context.housekeeper_api_ = housekeeper
    cg_context.meta_apis["compress_api"] = compress_api

    # GIVEN samples available for compression
    sample1: Sample = create_autospec(Sample, internal_id="sample1")
    samples: list[Sample] = [sample1]
    get_samples_mock = mocker.patch.object(
        fastq_module, "get_samples_available_for_compression", return_value=samples
    )
    compress_samples_mock = mocker.patch.object(
        fastq_module, "compress_fastq_to_spring_for_samples"
    )

    # WHEN running the compress fastq command with a case id
    result: Result = cli_runner.invoke(fastq_cmd, ["--case-id", "case_id"], obj=cg_context)

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN samples were fetched using the given case id
    get_samples_mock.assert_called_once_with(
        store=store, housekeeper=housekeeper, case_id="case_id"
    )

    # THEN the samples were sent for compression using the default limit
    compress_samples_mock.assert_called_once_with(
        compress_api=compress_api, samples=samples, sample_limit=5
    )


def test_compress_fastq_cli_case_id_no_samples(
    cli_runner: CliRunner, cg_context: CGConfig, mocker: MockFixture
):
    # GIVEN a store, housekeeper api and compress api on the context
    store: Store = create_autospec(Store)
    housekeeper: HousekeeperAPI = create_autospec(HousekeeperAPI)
    compress_api: CompressAPI = create_autospec(CompressAPI)
    cg_context.status_db_ = store
    cg_context.housekeeper_api_ = housekeeper
    cg_context.meta_apis["compress_api"] = compress_api

    # GIVEN no samples available for compression for the given case id
    get_samples_mock = mocker.patch.object(
        fastq_module, "get_samples_available_for_compression", return_value=[]
    )
    compress_samples_mock = mocker.patch.object(
        fastq_module, "compress_fastq_to_spring_for_samples"
    )

    # WHEN running the compress fastq command with a case id
    result: Result = cli_runner.invoke(fastq_cmd, ["--case-id", "case_id"], obj=cg_context)

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN samples were fetched using the given case id
    get_samples_mock.assert_called_once_with(
        store=store, housekeeper=housekeeper, case_id="case_id"
    )

    # THEN no samples were sent for compression
    compress_samples_mock.assert_not_called()


def test_compress_fastq_cli_sample_limit(
    cli_runner: CliRunner, cg_context: CGConfig, mocker: MockFixture
):
    # GIVEN a store, housekeeper api and compress api on the context
    store: Store = create_autospec(Store)
    housekeeper: HousekeeperAPI = create_autospec(HousekeeperAPI)
    compress_api: CompressAPI = create_autospec(CompressAPI)
    cg_context.status_db_ = store
    cg_context.housekeeper_api_ = housekeeper
    cg_context.meta_apis["compress_api"] = compress_api

    # GIVEN more samples available for compression than the given limit
    sample1: Sample = create_autospec(Sample, internal_id="sample1")
    sample2: Sample = create_autospec(Sample, internal_id="sample2")
    sample3: Sample = create_autospec(Sample, internal_id="sample3")
    samples: list[Sample] = [sample1, sample2, sample3]
    mocker.patch.object(fastq_module, "get_samples_available_for_compression", return_value=samples)

    # WHEN running the compress fastq command with a sample limit of two
    result: Result = cli_runner.invoke(fastq_cmd, ["--number-of-samples", "2"], obj=cg_context)

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN only the first two samples, within the limit, were sent for compression
    assert compress_api.compress_fastq.call_args_list == [
        call(sample_id=sample1.internal_id),
        call(sample_id=sample2.internal_id),
    ]


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
