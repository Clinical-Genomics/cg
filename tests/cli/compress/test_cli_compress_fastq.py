"""Tests for the compress fastq cli."""

import datetime as dt
from unittest.mock import Mock, call, create_autospec

import pytest
from click.testing import CliRunner, Result
from pytest_mock import MockFixture

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.compress import fastq as fastq_module
from cg.cli.compress.fastq import clean_fastq, fastq_cmd
from cg.cli.compress.helpers import (
    compress_fastq_to_spring_for_samples,
    get_samples_available_for_compression,
)
from cg.meta.compress import CompressAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


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

    # THEN samples were fetched using the right settings
    get_samples_mock.assert_called_once_with(
        store=store, housekeeper=housekeeper, age_limit_days=60, case_id=None
    )

    # THEN the samples were sent for compression using the default settings
    compress_samples_mock.assert_called_once_with(
        compress_api=compress_api, samples=samples, sample_limit=5, dry_run=False
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

    # THEN samples were fetched using the right settings
    get_samples_mock.assert_called_once_with(
        store=store, housekeeper=housekeeper, age_limit_days=60, case_id=None
    )

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

    # THEN samples were fetched using the right settings
    get_samples_mock.assert_called_once_with(
        store=store, housekeeper=housekeeper, age_limit_days=60, case_id="case_id"
    )

    # THEN the samples were sent for compression using the default limit
    compress_samples_mock.assert_called_once_with(
        compress_api=compress_api, samples=samples, sample_limit=5, dry_run=False
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

    # THEN samples were fetched using the right settings
    get_samples_mock.assert_called_once_with(
        store=store, housekeeper=housekeeper, age_limit_days=60, case_id="case_id"
    )

    # THEN no samples were sent for compression
    compress_samples_mock.assert_not_called()


def test_compress_fastq_cli_sample_all_flags(
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
    get_samples_mock = mocker.patch.object(
        fastq_module, "get_samples_available_for_compression", return_value=samples
    )
    compress_samples_mock = mocker.patch.object(
        fastq_module, "compress_fastq_to_spring_for_samples"
    )

    # WHEN running the compress fastq command with all custom settings
    result: Result = cli_runner.invoke(
        fastq_cmd,
        ["--number-of-samples", "2", "--dry-run", "--days-back", "1337", "--case-id", "case_id"],
        obj=cg_context,
    )

    # THEN samples were fetched using the right settings
    get_samples_mock.assert_called_once_with(
        store=store, housekeeper=housekeeper, age_limit_days=1337, case_id="case_id"
    )

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN the samples were sent for compression using the special limit
    compress_samples_mock.assert_called_once_with(
        compress_api=compress_api, samples=samples, sample_limit=2, dry_run=True
    )


@pytest.mark.freeze_time
def test_get_samples_available_for_compression():
    # GIVEN list of sample ids
    internal_ids: list[str] = ["sample1", "sample2"]

    # GIVEN a mocked housekeeper api
    housekeeper: TypedMock[HousekeeperAPI] = create_typed_mock(HousekeeperAPI)

    # GIVEN that the housekeeper bundles for the samples above contain fastq files
    housekeeper.as_type.get_bundle_names_with_fastq_files = Mock(return_value=internal_ids)

    # GIVEN a store
    store: TypedMock[Store] = create_typed_mock(Store)

    # GIVEN an expected cut-off date, 60 days ago
    expected_date = dt.datetime.now() - dt.timedelta(days=60)

    # WHEN getting samples available for compression
    get_samples_available_for_compression(
        store=store.as_type, housekeeper=housekeeper.as_type, age_limit_days=60
    )

    # THEN the correct calls was made
    housekeeper.as_mock.get_bundle_names_with_fastq_files.assert_called_once()
    store.as_mock.get_compressible_samples_by_internal_ids.assert_called_once_with(
        internal_ids=internal_ids, case_created_before_date=expected_date
    )


@pytest.mark.freeze_time("1822-09-18 13:37")
def test_get_samples_available_for_compression_input_case():
    # GIVEN list of sample ids
    internal_ids: list[str] = ["sample1", "sample2"]

    # GIVEN a housekeeper api
    housekeeper: HousekeeperAPI = create_autospec(HousekeeperAPI)

    # GIVEN a store
    store: TypedMock[Store] = create_typed_mock(Store)

    # GIVEN a case linked to two samples
    sample1: Sample = create_autospec(Sample, internal_id="sample1")
    sample2: Sample = create_autospec(Sample, internal_id="sample2")
    case: Case = create_autospec(Case, internal_id="case_id", samples=[sample1, sample2])

    # GIVEN that the case can be found
    store.as_type.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a date 60 days ago
    expected_date = dt.datetime(1822, 7, 20, 13, 37)

    # WHEN getting samples available for compression with a case id
    get_samples_available_for_compression(
        store=store.as_type,
        housekeeper=housekeeper,
        age_limit_days=60,
        case_id="case_id",
    )

    # THEN the correct calls was made
    store.as_mock.get_compressible_samples_by_internal_ids.assert_called_once_with(
        internal_ids=internal_ids, case_created_before_date=expected_date
    )


def test_get_samples_available_for_compression_missing_samples():
    # GIVEN a housekeeper api
    housekeeper: TypedMock[HousekeeperAPI] = create_typed_mock(HousekeeperAPI)

    # GIVEN that there are no bundles containing fastq files
    housekeeper.as_type.get_bundle_names_with_fastq_files = Mock(return_value=[])

    # GIVEN a store
    store: TypedMock[Store] = create_typed_mock(Store)

    # WHEN getting samples available for compression
    get_samples_available_for_compression(
        store=store.as_type, housekeeper=housekeeper.as_type, age_limit_days=60
    )

    # THEN the correct calls was made
    housekeeper.as_mock.get_bundle_names_with_fastq_files.assert_called_once()
    store.as_mock.get_compressible_samples_by_internal_ids.assert_not_called()


def test_get_samples_available_for_compression_input_case_missing_samples():
    # GIVEN a housekeeper api
    housekeeper: HousekeeperAPI = create_autospec(HousekeeperAPI)

    # GIVEN a store
    store: TypedMock[Store] = create_typed_mock(Store)

    # GIVEN that no samples is linked to the input case
    case: Case = create_autospec(Case, internal_id="case_id", links=[])

    # WHEN getting samples available for compression with a case id
    get_samples_available_for_compression(
        store=store.as_type, housekeeper=housekeeper, age_limit_days=60, case_id=case.internal_id
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
        sample_limit=2,
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


def test_compress_fastq_to_spring_for_samples_with_dry_run():
    # GIVEN compress api
    compress_api: TypedMock[CompressAPI] = create_typed_mock(CompressAPI)

    # GIVEN a sample
    sample1: Sample = create_autospec(Sample, internal_id="sample1")
    samples: list[Sample] = [sample1]

    # WHEN compressing samples with a sample limit of one
    compress_fastq_to_spring_for_samples(
        compress_api=compress_api.as_type,
        samples=samples,
        sample_limit=1,
        dry_run=True,
    )

    # THEN compression was called
    compress_api.as_mock.compress_fastq.assert_called_once_with(sample_id=sample1.internal_id)

    # THEN dry-run was enforced
    compress_api.as_mock.set_dry_run.assert_called_once_with(dry_run=True)


def test_compress_clean_cli(cli_runner: CliRunner, cg_context: CGConfig, mocker: MockFixture):
    # GIVEN a store, housekeeper api and compress api on the context
    store: TypedMock[Store] = create_typed_mock(Store)
    housekeeper: TypedMock[HousekeeperAPI] = create_typed_mock(HousekeeperAPI)
    compress_api: TypedMock[CompressAPI] = create_typed_mock(CompressAPI)

    cg_context.status_db_ = store.as_type
    cg_context.housekeeper_api_ = housekeeper.as_type
    cg_context.meta_apis["compress_api"] = compress_api.as_type

    # GIVEN samples available for compression
    sample1: Sample = create_autospec(Sample, internal_id="sample1")
    sample2: Sample = create_autospec(Sample, internal_id="sample2")
    samples: list[Sample] = [sample1, sample2]

    get_samples_mock = mocker.patch.object(
        fastq_module, "get_samples_available_for_compression", return_value=samples
    )

    # WHEN running the clean fastq command
    result: Result = cli_runner.invoke(clean_fastq, [], obj=cg_context)

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN function getting the samples is called with the right settings
    get_samples_mock.assert_called_once_with(
        store=store.as_type, housekeeper=housekeeper.as_type, age_limit_days=60, case_id=None
    )

    # THEN the samples fastq files where cleaned using the default settings
    compress_api.as_mock.clean_fastq_files_for_samples.assert_called_once_with(
        samples=samples, days_back=60
    )


def test_compress_clean_cli_case(cli_runner: CliRunner, cg_context: CGConfig, mocker: MockFixture):
    # GIVEN a store, housekeeper api and compress api on the context
    store: TypedMock[Store] = create_typed_mock(Store)
    housekeeper: TypedMock[HousekeeperAPI] = create_typed_mock(HousekeeperAPI)
    compress_api: TypedMock[CompressAPI] = create_typed_mock(CompressAPI)

    cg_context.status_db_ = store.as_type
    cg_context.housekeeper_api_ = housekeeper.as_type
    cg_context.meta_apis["compress_api"] = compress_api.as_type

    # GIVEN samples available for compression
    sample1: Sample = create_autospec(Sample, internal_id="sample1")
    sample2: Sample = create_autospec(Sample, internal_id="sample2")
    samples: list[Sample] = [sample1, sample2]

    get_samples_mock = mocker.patch.object(
        fastq_module, "get_samples_available_for_compression", return_value=samples
    )

    # WHEN running the clean fastq command
    result: Result = cli_runner.invoke(clean_fastq, ["--case-id", "case_id"], obj=cg_context)

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN function getting the samples is called with the right settings
    get_samples_mock.assert_called_once_with(
        store=store.as_type, housekeeper=housekeeper.as_type, age_limit_days=60, case_id="case_id"
    )

    # THEN the samples fastq files were cleand using the default settings
    compress_api.as_mock.clean_fastq_files_for_samples.assert_called_once_with(
        samples=samples, days_back=60
    )


def test_compress_clean_cli_dry_run(
    cli_runner: CliRunner, cg_context: CGConfig, mocker: MockFixture
):
    # GIVEN a store, housekeeper api and compress api on the context
    store: TypedMock[Store] = create_typed_mock(Store)
    housekeeper: TypedMock[HousekeeperAPI] = create_typed_mock(HousekeeperAPI)
    compress_api: TypedMock[CompressAPI] = create_typed_mock(CompressAPI)

    cg_context.status_db_ = store.as_type
    cg_context.housekeeper_api_ = housekeeper.as_type
    cg_context.meta_apis["compress_api"] = compress_api.as_type

    # GIVEN samples available for compression
    sample1: Sample = create_autospec(Sample, internal_id="sample1")
    sample2: Sample = create_autospec(Sample, internal_id="sample2")
    samples: list[Sample] = [sample1, sample2]

    get_samples_mock = mocker.patch.object(
        fastq_module, "get_samples_available_for_compression", return_value=samples
    )
    update_compress_api_mock = mocker.patch.object(fastq_module, "update_compress_api")

    # WHEN running the clean fastq command
    result: Result = cli_runner.invoke(clean_fastq, ["--dry-run"], obj=cg_context)

    # THEN the command exits successfully
    assert result.exit_code == 0

    # THEN update compress api is called with the right settings
    update_compress_api_mock.assert_called_once_with(compress_api.as_type, dry_run=True)

    # THEN function getting the samples is called with the right settings
    get_samples_mock.assert_called_once_with(
        store=store.as_type, housekeeper=housekeeper.as_type, age_limit_days=60, case_id=None
    )

    # THEN the samples fastq files were cleand using the default settings
    compress_api.as_mock.clean_fastq_files_for_samples.assert_called_once_with(
        samples=samples, days_back=60
    )
