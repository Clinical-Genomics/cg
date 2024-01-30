"""Tests for the transfer of external data."""

import logging
from pathlib import Path

from housekeeper.store.models import Bundle, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.transfer.external_data import ExternalDataAPI
from cg.store.models import Case, Sample
from cg.store.store import Store
from cg.utils.checksum.checksum import check_md5sum, extract_md5sum
from tests.store.conftest import sample_obj
from tests.store_helpers import StoreHelpers


def test_create_log_dir(caplog, external_data_api: ExternalDataAPI, ticket_id: str):
    """Test generating the directory for logging."""
    caplog.set_level(logging.INFO)

    # WHEN the log directory is created
    log_dir = external_data_api.create_log_dir(ticket=ticket_id)

    # THEN the path is not created since it is a dry run
    assert "Would have created path" in caplog.text

    # THEN the created path should start with 2 dirs and then the ticket id
    assert str(log_dir).startswith(f"/another/path/{ticket_id}")


def test_get_source_path(
    cust_sample_id: str,
    customer_id: str,
    external_data_api: ExternalDataAPI,
    ticket_id: str,
):
    """Test generating the source path."""
    # GIVEN a ticket number a customer and a customer sample id

    # WHEN the function is called and assigned
    source_path = external_data_api.get_source_path(
        ticket=ticket_id,
        customer=customer_id,
        cust_sample_id=cust_sample_id,
    )

    # THEN the return should be
    assert source_path == Path("server.name.se:/path/cust000/on/caesar/123456/child/")


def test_get_destination_path(
    customer_id: str,
    external_data_api: ExternalDataAPI,
    sample_id: str,
):
    """Test generating the destination path."""
    # GIVEN a customer and an internal sample id
    # WHEN the function creates the destination path
    destination_path = external_data_api.get_destination_path(
        customer=customer_id, lims_sample_id=sample_id
    )

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

    mocker.patch.object(ExternalDataAPI, "get_source_path")
    external_data_api.get_source_path.return_value = external_data_directory

    external_data_api.source_path = str(Path("").joinpath(*external_data_directory.parts[:-2]))
    external_data_api.destination_path = str(
        Path("").joinpath(*external_data_directory.parts[:-1], "%s")
    )

    # WHEN the transfer is initiated
    external_data_api.transfer_sample_files_from_source(ticket=ticket_id)

    # THEN only the two samples present in the source directory are included in the rsync

    assert str(external_data_directory) in caplog.text


def test_get_all_fastq(external_data_api: ExternalDataAPI, external_data_directory: Path):
    """Test the finding of fastq.gz files in customer directories."""
    # GIVEN a folder containing two folders with both fastq and md5 files
    for folder in external_data_directory.iterdir():
        # WHEN the list of file paths is created
        files = external_data_api.get_all_fastq(
            sample_folder=external_data_directory.joinpath(folder)
        )
        # THEN only fast.gz files are returned
        assert all(tmp.suffixes == [".fastq", ".gz"] for tmp in files)


def test_get_failed_fastq_paths(external_data_api: ExternalDataAPI, fastq_file: Path):
    bad_md5sum_file_path: Path = fastq_file.parent.joinpath("fastq_run_R1_001.fastq.gz")
    # GIVEN a list of paths with one fastq_file with a correct md5sum and one with an incorrect md5sum
    # When the failed paths are extracted
    failed_paths: list[Path] = external_data_api.get_failed_fastq_paths(
        [fastq_file, bad_md5sum_file_path]
    )
    # THEN only the path to the failed file should be in the list
    assert failed_paths == [bad_md5sum_file_path]


def test_add_and_include_files_to_bundles(
    external_data_api: ExternalDataAPI,
    fastq_file: Path,
    hk_bundle_data: dict,
    sample_id: str,
    helpers: StoreHelpers,
):
    """Tests adding files to Housekeeper."""
    # GIVEN
    external_data_api.dry_run = False
    hk_api: HousekeeperAPI = external_data_api.housekeeper_api
    helpers.ensure_hk_version(hk_api, hk_bundle_data)

    # WHEN the file is added and included to Housekeeper
    external_data_api.add_and_include_files_to_bundles(
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
    external_data_api: ExternalDataAPI,
    fastq_file: Path,
    mocker,
    ticket_id: str,
):
    """Test adding and including samples from a case to Housekeeper."""
    # GIVEN an ExternalDataAPI with dry-run equals False
    external_data_api.dry_run = False
    # GIVEN a Store with a DNA case, which is available for analysis
    case: Case = external_data_api.status_db.get_case_by_internal_id(internal_id=case_id)
    mocker.patch.object(Store, "get_cases_by_ticket_id")
    Store.get_cases_by_ticket_id.return_value = [case]
    samples = [case_sample.sample for case_sample in case.links]

    # GIVEN a list of paths and only one sample being available
    mocker.patch.object(ExternalDataAPI, "get_all_paths")
    ExternalDataAPI.get_all_paths.return_value = [fastq_file]

    mocker.patch.object(Path, "iterdir")
    Path.iterdir.return_value = []

    mocker.patch.object(ExternalDataAPI, "get_available_samples")
    ExternalDataAPI.get_available_samples.return_value = samples[:-1]

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
    external_data_api: ExternalDataAPI,
    sample: Sample,
    ticket_id: str,
    tmpdir_factory,
):
    # GIVEN one such sample exists
    tmp_dir_path: Path = Path(tmpdir_factory.mktemp(sample.internal_id, numbered=False))
    available_samples = external_data_api.get_available_samples(
        folder=tmp_dir_path.parent, ticket=ticket_id
    )
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
    external_data_api: ExternalDataAPI,
    ticket_id: str,
    tmpdir_factory,
):
    # GIVEN that the empty directory created does not contain any correct folders
    tmp_dir_path: Path = Path(tmpdir_factory.mktemp("not_sample_id", numbered=False))
    available_samples = external_data_api.get_available_samples(
        folder=tmp_dir_path, ticket=ticket_id
    )
    # THEN the function should return an empty list
    assert available_samples == []


def test_checksum(fastq_file: Path):
    """Tests if the function correctly calculates md5sum and returns the correct result."""
    # GIVEN a fastq file with corresponding correct md5 file and a fastq file with a corresponding incorrect md5 file
    bad_md5sum_file_path: Path = fastq_file.parent.joinpath("fastq_run_R1_001.fastq.gz")

    # THEN a file with a correct md5 sum should return true
    assert check_md5sum(file_path=fastq_file, md5sum="a95cbb265540a2261fce941059784fd1")

    # THEN a file with an incorrect md5 sum should return false
    assert not check_md5sum(
        file_path=bad_md5sum_file_path, md5sum="c690b0124173772ec4cbbc43709d84ee"
    )


def test_extract_checksum(fastq_file: Path):
    """Tests if the function successfully extract the correct md5sum."""

    # GIVEN a file containing a md5sum
    md5sum_file = Path(f"{fastq_file.as_posix()}.md5")

    # WHEN extracting the md5sum

    # THEN the function should extract it
    assert extract_md5sum(md5sum_file=md5sum_file) == "a95cbb265540a2261fce941059784fd1"
