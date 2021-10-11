"""Tests for the transfer of external data"""
import logging
from pathlib import Path
from typing import List

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.meta.transfer.external_data import ExternalDataAPI
from cg.meta.transfer.md5sum import check_md5sum, extract_md5sum
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from tests.cli.workflow.conftest import dna_case
from tests.mocks.hk_mock import MockHousekeeperAPI


def test_create_log_dir(caplog, external_data_api: ExternalDataAPI, ticket_nr: int):
    """Test generating the directory for logging"""
    caplog.set_level(logging.INFO)

    # WHEN the log directory is created
    log_dir = external_data_api.create_log_dir(ticket_id=ticket_nr, dry_run=True)

    # THEN the path is not created since it is a dry run
    assert "Would have created path" in caplog.text

    # THEN the created path is
    assert str(log_dir).startswith("/another/path/123456")


def test_create_source_path(external_data_api: ExternalDataAPI, ticket_nr: int, customer_id: str):
    """Test generating the source path"""

    # WHEN the source path is created

    source_path = external_data_api.create_source_path(
        raw_path="/path/%s", ticket_id=ticket_nr, customer=customer_id, cust_sample_id="ABC123"
    )

    # THEN the source path is
    assert source_path == Path("/path/cust000/123456/ABC123/")


def test_create_destination_path(external_data_api: ExternalDataAPI, customer_id: str):
    """Test generating the destination path"""

    # WHEN the source path is created
    destination_path = external_data_api.create_destination_path(
        raw_path="/path/%s", customer=customer_id, lims_sample_id="ACC123"
    )

    # THEN the source path is
    assert destination_path == Path("/path/cust000/ACC123/")


def test_download_sample(
    external_data_api: ExternalDataAPI, mocker, ticket_nr: int, customer_id: str
):
    """Test for downloading external data via slurm"""

    # GIVEN paths needed to run rsync
    mocker.patch.object(ExternalDataAPI, "create_log_dir")
    ExternalDataAPI.create_log_dir.return_value = Path("/path/to/log")

    mocker.patch.object(ExternalDataAPI, "create_source_path")
    ExternalDataAPI.create_source_path.return_value = Path("/path/to/source")

    mocker.patch.object(ExternalDataAPI, "create_destination_path")
    ExternalDataAPI.create_destination_path.return_value = Path("/path/to/destination")

    # WHEN the destination path is created
    sbatch_number = external_data_api.transfer_sample(
        cust_sample_id="ABC123",
        ticket_id=ticket_nr,
        cust=customer_id,
        lims_sample_id="ACC123",
        dry_run=True,
    )

    # THEN check that an integer was returned as sbatch number
    assert isinstance(sbatch_number, int)


def test_get_all_fastq(
    cg_context: CGConfig, external_data_directory, external_data_api: ExternalDataAPI
):
    """Test the finding of fastq.gz files in customer directories."""
    for folder in external_data_directory.iterdir():
        # WHEN the list of file-paths is created
        files = external_data_api.get_all_fastq(
            sample_folder=external_data_directory.joinpath(folder)
        )
        # THEN only fast.gz files are returned
        assert [tmp.suffixes == [".fastq", ".gz"] for tmp in files]


def test_check_bundle_fastq_files(
    external_data_api: ExternalDataAPI, sample_id: str, hk_version_obj
):

    # GIVEN a housekeeper bundle with a file
    # mocker.patch.object(MockHousekeeperAPI, "get_files")
    # MockHousekeeperAPI.get_files.return_value = [Path("/boring/old/boomer/file.fastq.gz")]
    external_data_api.housekeeper_api.add_file(
        path=Path("/boring/old/boomer/file.fastq.gz"), tags=["fastq"], version_obj=hk_version_obj
    )

    # WHEN when attempting to add two files, one existing and one new
    files_to_add: List[Path] = external_data_api.check_bundle_fastq_files(
        fastq_paths=[Path("/wow/new/cool/file.fastq.gz"), Path("/boring/old/boomer/file.fastq.gz")],
        lims_sample_id=sample_id,
        last_version=hk_version_obj,
    )

    # Then only the new file should be returned
    assert files_to_add == [Path("/wow/new/cool/file.fastq.gz")]


def test_add_files_to_bundles(
    external_data_api: ExternalDataAPI, sample_id: str, hk_version_obj, fastq_file
):
    """Tests adding files to housekeeper and checking corresponding md5file."""
    # Given a fastq file that has a corresponding .md5 file with correct md5sum.

    # Then the function should return True and the file should be added.
    print(fastq_file)
    assert external_data_api.add_files_to_bundles(
        fastq_paths=[fastq_file], last_version=hk_version_obj, lims_sample_id=sample_id
    )
    assert str(fastq_file.absolute()) in [idx.path for idx in hk_version_obj.files]

    # Given a fastq file that has a corresponding .md5 file with incorrect md5sum.

    # Then the function should return False and no file should be added.
    bad_file = fastq_file.parent.joinpath("fastq_run_R1_001.fastq.gz")
    assert not external_data_api.add_files_to_bundles(
        fastq_paths=[bad_file], last_version=hk_version_obj, lims_sample_id=sample_id
    )
    assert str(bad_file.absolute()) not in [idx.path for idx in hk_version_obj.files]


def test_configure_housekeeper(
    external_data_api: ExternalDataAPI,
    mocker,
    case_id,
    ticket_nr,
    dna_case,
    # Do not remove dna_case fixture. It sets up Store with a case
):
    """Test adding samples from a case to Housekeeper."""
    # GIVEN a case is available for analysis
    cases = external_data_api.status_db.query(models.Family).filter(
        models.Family.internal_id == case_id
    )
    mocker.patch.object(Store, "get_cases_from_ticket")
    Store.get_cases_from_ticket.return_value = cases
    samples = [fam_sample.sample.internal_id for fam_sample in cases.all()[0].links]

    # GIVEN a list of paths
    mocker.patch.object(ExternalDataAPI, "get_all_paths")
    ExternalDataAPI.get_all_paths.return_value = [Path("/path/to/something/")]

    mocker.patch.object(MockHousekeeperAPI, "last_version")
    MockHousekeeperAPI.last_version.return_value = None

    mocker.patch.object(MockHousekeeperAPI, "get_files")
    MockHousekeeperAPI.get_files.return_value = []

    # THEN none of the cases should exist in housekeeper
    assert [external_data_api.housekeeper_api.bundle(sample) is None for sample in samples]

    # WHEN the sample bundles are added to housekeeper
    external_data_api.configure_housekeeper(ticket_id=ticket_nr)

    # THEN the sample bundles exist in housekeeper and that the file has been added to all bundles
    assert [external_data_api.housekeeper_api.bundle(sample) is not None for sample in samples]
    assert [
        external_data_api.housekeeper_api.bundle(sample).versions[0].files[0].path
        == "/path/to/something/"
        for sample in samples
    ]


def test_checksum(fastq_file: Path):
    """Tests if the function correctly calculates md5sum and returns the correct result."""
    # GIVEN a fastq file with corresponding correct md5 file and a fastq file with a corresponding incorrect md5 file

    # THEN a file with a correct md5 sum should return true
    assert check_md5sum(file_path=fastq_file, md5sum="a95cbb265540a2261fce941059784fd1")
    # THEN a file with an incorrect md5 sum should return false
    other_path: Path = fastq_file.parent.joinpath("fastq_run_R1_001.fastq.gz")
    assert not check_md5sum(file_path=other_path, md5sum="c690b0124173772ec4cbbc43709d84ee")


def test_extract_checksum(fastq_file: Path):
    """Tests if the function successfully extract the correct md5sum"""
    # Given a file containing an md5sum
    file = Path(str(fastq_file) + ".md5")
    # Then the function should extract it
    assert extract_md5sum(md5sum_file=file) == "a95cbb265540a2261fce941059784fd1"
