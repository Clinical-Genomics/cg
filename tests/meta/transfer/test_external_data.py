"""Tests for the transfer of external data."""

import logging
from pathlib import Path
from unittest.mock import Mock

from _pytest.logging import LogCaptureFixture
from housekeeper.store.models import Bundle, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.transfer.external_data import (
    AddExternalDataAPI,
    ExternalDataAPI,
    TransferExternalDataAPI,
)
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.store.conftest import sample_obj
from tests.store_helpers import StoreHelpers


def test_get_destination_path(
    customer_id: str,
    external_data_api: ExternalDataAPI,
    sample_id: str,
):
    """Test generating the destination path."""
    # GIVEN a customer and an internal sample id

    # WHEN the function creates the destination path
    destination_path = external_data_api.get_destination_path(sample_id=sample_id)

    # THEN the destination path should contain the customer_id, ticket_id and sample_id
    assert destination_path == Path("/path/on/hasta", customer_id, sample_id)


def test_create_log_dir(
    caplog,
    transfer_external_data_api: TransferExternalDataAPI,
    ticket_id: str,
    hasta_external_dir: Path,
):
    """Test generating the directory for logging."""
    caplog.set_level(logging.INFO)

    # GIVEN a transfer API initialised with a ticket and dry run equals True

    # WHEN the log directory is created
    log_dir = transfer_external_data_api.create_log_dir()

    # THEN the path is not created since it is a dry run
    assert "Would have created path" in caplog.text

    # THEN the created path should start with 2 dirs and then the ticket id
    assert str(log_dir).startswith(f"/another/path/{ticket_id}")


def test_get_source_path(
    cust_sample_id: str, transfer_external_data_api: TransferExternalDataAPI, ticket_id: str
):
    """Test generating the source path."""
    # GIVEN a transfer API and a sample id

    # WHEN getting the source path
    source_path = transfer_external_data_api.get_source_path(
        sample_id=cust_sample_id,
    )

    # THEN the return should be
    assert source_path == Path("server.name.se:/path/cust000/on/caesar", ticket_id, cust_sample_id)


def test_transfer_sample_files_from_source(
    caplog,
    customer_id: str,
    cust_sample_id: str,
    transfer_external_data_api: TransferExternalDataAPI,
    external_data_directory: Path,
    helpers,
    mocker,
    ticket_id: str,
):
    caplog.set_level(logging.INFO)

    # GIVEN a Store with three samples, where only two samples are present in the source folder
    for sample in [f"{cust_sample_id}1", f"{cust_sample_id}2", f"{cust_sample_id}3"]:
        helpers.add_sample(
            store=transfer_external_data_api.status_db, name=sample, original_ticket=ticket_id
        )

    mocker.patch.object(Store, "get_customer_id_from_ticket")
    Store.get_customer_id_from_ticket.return_value = customer_id

    mocker.patch.object(TransferExternalDataAPI, "get_source_path")
    transfer_external_data_api.get_source_path.return_value = external_data_directory

    transfer_external_data_api.source_path = str(
        Path("").joinpath(*external_data_directory.parts[:-2])
    )
    transfer_external_data_api._destination_path = str(
        Path("").joinpath(*external_data_directory.parts[:-1], "%s")
    )

    # WHEN the transfer is initiated
    transfer_external_data_api.transfer_sample_files_from_source()

    # THEN only the two samples present in the source directory are included in the rsync
    assert str(external_data_directory) in caplog.text


def test_add_and_include_files_to_bundles(
    add_external_data_api: AddExternalDataAPI,
    fastq_file: Path,
    hk_bundle_data: dict,
    sample_id: str,
    helpers: StoreHelpers,
):
    """Tests adding files to Housekeeper."""
    # GIVEN
    add_external_data_api.dry_run = False
    hk_api: HousekeeperAPI = add_external_data_api.housekeeper_api
    helpers.ensure_hk_version(hk_api, hk_bundle_data)

    # WHEN the file is added and included to Housekeeper
    add_external_data_api.add_and_include_files_to_bundles(
        fastq_paths=[fastq_file],
        lims_sample_id=sample_id,
    )

    # THEN the file should have been added to Housekeeper
    version: Version = hk_api.last_version(bundle=sample_id)
    file_path = Path(version.relative_root_dir, fastq_file.name)
    assert file_path.as_posix() in [file.path for file in version.files]

    # THEN the file should have been included to Housekeeper
    assert Path(hk_api.root_dir, file_path).exists()


def test_add_transfer_to_housekeeper(
    case_id,
    add_external_data_api: AddExternalDataAPI,
    fastq_file: Path,
    mocker,
    ticket_id: str,
):
    """Test adding and including samples from a case to Housekeeper."""
    # GIVEN an AddExternalDataAPI

    # GIVEN a Store with a DNA case, which is available for analysis
    case: Case = add_external_data_api.status_db.get_case_by_internal_id(internal_id=case_id)
    mocker.patch.object(Store, "get_cases_by_ticket_id")
    Store.get_cases_by_ticket_id.return_value = [case]
    sample_ids: list[str] = [case_sample.sample.internal_id for case_sample in case.links]

    # GIVEN a list of paths and only one sample being available
    mocker.patch.object(AddExternalDataAPI, "get_all_paths")
    AddExternalDataAPI.get_all_paths.return_value = [fastq_file]

    mocker.patch.object(Path, "iterdir")
    Path.iterdir.return_value = []

    mocker.patch.object(AddExternalDataAPI, "get_available_samples")
    AddExternalDataAPI.get_available_sample_ids.return_value = sample_ids[:-1]

    mocker.patch.object(Store, "set_case_action")
    Store.set_case_action.return_value = None

    # GIVEN that none of the samples should exist in housekeeper
    assert all(
        external_data_api.housekeeper_api.bundle(sample.internal_id) is None for sample in samples
    )

    # WHEN the sample bundles are added to housekeeper
    external_data_api.add_transfer_to_housekeeper(ticket=ticket_id)

    # THEN sample bundles exist in housekeeper and the file has been added to those bundles
    added_bundles: list[Bundle] = external_data_api.housekeeper_api.bundles().all()
    assert all(
        sample.internal_id in [bundle.name for bundle in added_bundles] for sample in samples[:-1]
    )
    assert all(
        Path(bundle.versions[0].files[0].path).name == str(fastq_file.name)
        for bundle in added_bundles
    )
    # THEN the sample that is not available should not exist
    assert samples[-1].internal_id not in [added_sample.name for added_sample in added_bundles]


def test_get_available_samples(
    add_external_data_api: AddExternalDataAPI,
    sample: Sample,
    ticket_id: str,
    tmpdir_factory,
):
    # GIVEN one such sample exists
    tmp_dir_path: Path = Path(tmpdir_factory.mktemp(sample.internal_id, numbered=False))
    available_samples = add_external_data_api.get_available_sample_ids()
    # THEN the function should return a list containing the sample object
    assert available_samples == [sample]
    tmp_dir_path.rmdir()


def test_curate_sample_folder(
    case_id, customer_id, external_data_api: ExternalDataAPI, tmpdir_factory
):
    case = external_data_api.status_db.get_case_by_internal_id(internal_id=case_id)
    sample: Sample = case.links[0].sample
    tmp_folder = Path(tmpdir_factory.mktemp(sample.name, numbered=False))
    external_data_api.curate_sample_folder(
        customer_id=customer_id, sample_folder=tmp_folder, force=False
    )
    assert (tmp_folder.parent / sample.internal_id).exists()
    assert not tmp_folder.exists()


def test_get_available_samples_no_samples_avail(
    add_external_data_api: AddExternalDataAPI,
    ticket_id: str,
    tmpdir_factory,
):
    # GIVEN that the empty directory created does not contain any correct folders
    tmp_dir_path: Path = Path(tmpdir_factory.mktemp("not_sample_id", numbered=False))
    available_samples = add_external_data_api.get_available_sample_ids(
        folder=tmp_dir_path, ticket=ticket_id
    )
    # THEN the function should return an empty list
    assert available_samples == []


def test_add_fastqs_to_housekeeper_and_start_cases_valid_files(
    add_external_data_api: AddExternalDataAPI, mocker: Mock, external_data_directory: Path
):
    """Test that files are added to Housekeeper and cases are started when all fastqs are valid."""

    # GIVEN a list of fastq files
    mocker.patch.object(AddExternalDataAPI, "add_and_include_files_to_bundles")
    mocker.patch.object(AddExternalDataAPI, "start_cases")
    mocker.patch.object(
        AddExternalDataAPI,
        "get_destination_path",
        return_value=external_data_directory,
    )

    # WHEN the function is called
    add_external_data_api.add_fastqs_to_housekeeper_and_start_cases()
    # THEN the files should be added to Housekeeper and the cases should be started
    add_external_data_api.add_and_include_files_to_bundles.assert_called_once()
    add_external_data_api.start_cases.assert_called_once()


def test_add_fastqs_to_housekeeper_and_start_cases_invalid_files(
    add_external_data_api: AddExternalDataAPI, caplog: LogCaptureFixture
):
    """
    Test that files are not added to Housekeeper and cases are not started when any fastq is
    invalid.
    """
    # GIVEN a list of fastq files where one is invalid
    # WHEN the function is called
    # THEN no files should be added to Housekeeper and no cases should be started
    assert (
        "Changes in housekeeper will not be committed and no cases will be started" in caplog.text
    )
