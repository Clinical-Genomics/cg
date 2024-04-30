"""Tests for the transfer of external data."""

import logging
from pathlib import Path

from cg.meta.transfer.external_data import ExternalDataAPI
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.cli.workflow.conftest import dna_case
from tests.mocks.hk_mock import MockHousekeeperAPI
from tests.store.conftest import sample_obj


def test_create_log_dir_dry_run(caplog, external_data_api: ExternalDataAPI, ticket_id: str):
    """Test that the directory for logging would have been created."""
    caplog.set_level(logging.INFO)
    # GIVEN an External API with a ticket and dry run set to True
    external_data_api.ticket = ticket_id
    external_data_api.dry_run = True

    # WHEN the log directory is created
    log_dir = external_data_api._create_log_dir()

    # THEN the path is not created since it is a dry run
    assert "Would have created path" in caplog.text

    # THEN the path should start with 2 dirs and then the ticket id
    assert str(log_dir).startswith(f"/another/path/{ticket_id}")


def test_get_source_path(
    cust_sample_id: str,
    customer_id: str,
    external_data_api: ExternalDataAPI,
    ticket_id: str,
):
    """Test generating the source path."""
    # GIVEN an External API with a ticket number, a customer and a customer sample id
    external_data_api.ticket = ticket_id
    customer_id: str = external_data_api.status_db.get_customer_id_from_ticket(ticket=ticket_id)
    external_data_api.customer_id = customer_id

    # WHEN the function is called and assigned
    source_path = external_data_api._get_source_path(cust_sample_id=cust_sample_id)

    # THEN the return should be
    assert source_path == Path("server.name.se:/path/cust000/on/caesar/123456/child/")


def test_get_destination_path(
    customer_id: str,
    external_data_api: ExternalDataAPI,
    sample_id: str,
):
    """Test generating the destination path."""
    # GIVEN an External API with a customer id and an internal sample id
    external_data_api.customer_id = customer_id
    # WHEN the function creates the destination path
    destination_path = external_data_api._get_destination_path(lims_sample_id=sample_id)

    # THEN the destination path should contain the customer_id, ticket_id and sample_id
    assert destination_path == Path("/path/on/hasta/cust000/ADM1/")


def test_transfer_sample_files_from_source(
    caplog,
    customer_id: str,
    cust_sample_id: str,
    external_data_api: ExternalDataAPI,
    external_data_directory: Path,
    helpers,
    mocker,
    ticket_id: str,
):
    caplog.set_level(logging.INFO)

    # GIVEN a Store with three samples, where only two samples are present in the source folder
    for sample in [f"{cust_sample_id}1", f"{cust_sample_id}2", f"{cust_sample_id}3"]:
        helpers.add_sample(
            store=external_data_api.status_db, name=sample, original_ticket=ticket_id
        )

    mocker.patch.object(Store, "get_customer_id_from_ticket")
    Store.get_customer_id_from_ticket.return_value = customer_id

    mocker.patch.object(ExternalDataAPI, "_get_source_path")
    external_data_api._get_source_path.return_value = external_data_directory

    external_data_api.source_path = str(Path("").joinpath(*external_data_directory.parts[:-2]))
    external_data_api.destination_path = str(
        Path("").joinpath(*external_data_directory.parts[:-1], "%s")
    )

    # WHEN the transfer is initiated
    external_data_api.transfer_sample_files_from_source(ticket=ticket_id, dry_run=True)

    # THEN only the two samples present in the source directory are included in the rsync

    assert str(external_data_directory) in caplog.text


def test_add_transfer_to_housekeeper(
    case_id,
    external_data_api: ExternalDataAPI,
    fastq_file: Path,
    mocker,
    ticket_id: str,
):
    """Test adding samples from a case to Housekeeper"""
    # GIVEN a Store with a DNA case, which is available for analysis
    case = external_data_api.status_db.get_case_by_internal_id(internal_id=case_id)
    mocker.patch.object(Store, "get_cases_by_ticket_id")
    Store.get_cases_by_ticket_id.return_value = [case]
    samples = [fam_sample.sample for fam_sample in case.links]

    # GIVEN a list of paths and only two samples being available
    mocker.patch.object(ExternalDataAPI, "_get_fastq_paths_to_add")
    ExternalDataAPI._get_fastq_paths_to_add.return_value = [fastq_file]

    mocker.patch.object(MockHousekeeperAPI, "last_version")
    MockHousekeeperAPI.last_version.return_value = None

    mocker.patch.object(MockHousekeeperAPI, "get_files")
    MockHousekeeperAPI.get_files.return_value = []

    mocker.patch.object(Path, "iterdir")
    Path.iterdir.return_value = []

    mocker.patch.object(ExternalDataAPI, "_get_available_sample_ids")
    ExternalDataAPI._get_available_sample_ids.return_value = [
        sample.internal_id for sample in samples[:-1]
    ]

    mocker.patch.object(Store, "set_case_action")
    Store.set_case_action.return_value = None

    # THEN none of the samples should exist in housekeeper
    assert all(
        external_data_api.housekeeper_api.bundle(sample.internal_id) is None for sample in samples
    )

    # WHEN the sample bundles are added to housekeeper
    external_data_api.add_transfer_to_housekeeper(ticket=ticket_id)

    # THEN two sample bundles exist in housekeeper and the file has been added to those bundles bundles
    added_samples = list(external_data_api.housekeeper_api.bundles())
    assert all(
        sample.internal_id in [added_sample.name for added_sample in added_samples]
        for sample in samples[:-1]
    )
    assert all(
        sample.versions[0].files[0].path == str(fastq_file.absolute()) for sample in added_samples
    )
    # Then the sample that is not available should not exists
    assert samples[-1].internal_id not in [added_sample.name for added_sample in added_samples]


def test_get_sample_ids_from_folder(
    external_data_api: ExternalDataAPI,
    sample: Sample,
    ticket_id: str,
    tmpdir_factory,
):
    # GIVEN one such sample exists
    tmp_dir_path: Path = Path(tmpdir_factory.mktemp(sample.internal_id, numbered=False))
    external_data_api.ticket = ticket_id
    available_samples = external_data_api._get_sample_ids_from_folder(folder=tmp_dir_path.parent)
    # THEN the function should return a list containing the sample object
    assert available_samples == [sample.internal_id]
    tmp_dir_path.rmdir()


def test_curate_sample_folder(
    case_id: str, customer_id: str, external_data_api: ExternalDataAPI, tmpdir_factory
):
    # GIVEN a External API with a customer id
    external_data_api.force = False
    external_data_api.customer_id = customer_id

    # GIVEN a case with a sample
    case: Case = external_data_api.status_db.get_case_by_internal_id(internal_id=case_id)
    sample: Sample = case.links[0].sample
    assert sample

    # GIVEN that the sample folder has the sample name
    tmp_folder = Path(tmpdir_factory.mktemp(sample.name, numbered=False))

    # WHEN the sample folder is curated
    external_data_api._curate_sample_folder(sample_folder=tmp_folder)

    # THEN the sample folder with the sample name does not exist anymore
    assert not tmp_folder.exists()
    # THEN the sample folder with the sample internal id exists
    assert (tmp_folder.parent / sample.internal_id).exists()


def test_get_sample_ids_from_folder_no_samples_available(
    external_data_api: ExternalDataAPI,
    ticket_id: str,
    tmpdir_factory,
):
    # GIVEN that the empty directory created does not contain any correct folders
    tmp_dir_path: Path = Path(tmpdir_factory.mktemp("not_sample_id", numbered=False))
    external_data_api.ticket = ticket_id
    available_samples = external_data_api._get_sample_ids_from_folder(folder=tmp_dir_path)
    # THEN the function should return an empty list
    assert available_samples == []
