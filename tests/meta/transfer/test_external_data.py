"""Tests for the transfer of external data"""
import logging
from pathlib import Path

from cg.meta.transfer.external_data import ExternalDataAPI
from cg.meta.transfer.md5sum import check_md5sum, extract_md5sum
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from tests.mocks.hk_mock import MockHousekeeperAPI
from tests.cli.workflow.conftest import dna_case


def test_create_log_dir(caplog, external_data_api: ExternalDataAPI, ticket_nr: int):
    """Test generating the directory for logging"""
    caplog.set_level(logging.INFO)

    # WHEN the log directory is created
    log_dir = external_data_api.create_log_dir(ticket_id=ticket_nr, dry_run=True)

    # THEN the path is not created since it is a dry run
    assert "Would have created path" in caplog.text

    # THEN the created path should start with 2 dirs and then the ticket id
    assert str(log_dir).startswith("/another/path/123456")


def test_get_source_path(
    cust_sample_id: str,
    customer_id: str,
    external_data_api: ExternalDataAPI,
    ticket_nr: int,
):
    """Test generating the source path"""
    # GIVEN a ticket number a customer and a customer sample id

    # WHEN the function is called and assigned
    source_path = external_data_api.get_source_path(
        ticket_id=ticket_nr,
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
    """Test generating the destination path"""
    # GIVEN a customer and an internal sample id
    # WHEN the function creates the destination path
    destination_path = external_data_api.get_destination_path(
        customer=customer_id, lims_sample_id=sample_id
    )

    # THEN the destination path should contain the customer_id, ticket_id and sample_id
    assert destination_path == Path("/path/on/hasta/cust000/ADM1/")


def test_download_sample(
    apps_dir: Path,
    customer_id: str,
    cust_sample_id: str,
    external_data_api: ExternalDataAPI,
    mocker,
    sample_id: str,
    ticket_nr: int,
):
    """Test for transferring external data via SLURM"""

    # GIVEN paths needed to run rsync
    mocker.patch.object(ExternalDataAPI, "create_log_dir")
    ExternalDataAPI.create_log_dir.return_value = apps_dir

    mocker.patch.object(ExternalDataAPI, "get_source_path")
    ExternalDataAPI.get_source_path.return_value = apps_dir

    mocker.patch.object(ExternalDataAPI, "get_destination_path")
    ExternalDataAPI.get_destination_path.return_value = apps_dir

    # WHEN the samples are transferred
    sbatch_number = external_data_api.transfer_sample(
        cust_sample_id=cust_sample_id,
        ticket_id=ticket_nr,
        cust=customer_id,
        lims_sample_id=sample_id,
        dry_run=True,
    )

    # THEN check that an integer was returned
    assert isinstance(sbatch_number, int)


def test_get_all_fastq(
    cg_context: CGConfig, external_data_api: ExternalDataAPI, external_data_directory
):
    """Test the finding of fastq.gz files in customer directories"""
    # GIVEN a folder containing two folders with both fastq and md5 files
    for folder in external_data_directory.iterdir():
        # WHEN the list of file paths is created
        files = external_data_api.get_all_fastq(
            sample_folder=external_data_directory.joinpath(folder)
        )
        # THEN only fast.gz files are returned
        assert all([tmp.suffixes == [".fastq", ".gz"] for tmp in files])


def test_add_files_to_bundles(
    external_data_api: ExternalDataAPI, fastq_file: Path, hk_version_obj, sample_id: str
):
    """Tests adding files to housekeeper"""
    # GIVEN a file to be added
    to_be_added = [fastq_file]

    # WHEN the files are added.
    external_data_api.add_files_to_bundles(
        fastq_paths=to_be_added, last_version=hk_version_obj, lims_sample_id=sample_id
    )

    # THEN the function should return True and the file should be added.
    assert str(fastq_file.absolute()) in [idx.path for idx in hk_version_obj.files]


def test_add_transfer_to_housekeeper(
    case_id, dna_case, external_data_api: ExternalDataAPI, fastq_file: Path, mocker, ticket_nr
):
    """Test adding samples from a case to Housekeeper"""
    # GIVEN a Store with a DNA case, which is available for analysis
    cases = external_data_api.status_db.query(models.Family).filter(
        models.Family.internal_id == case_id
    )
    mocker.patch.object(Store, "get_cases_from_ticket")
    Store.get_cases_from_ticket.return_value = cases
    samples = [fam_sample.sample.internal_id for fam_sample in cases.all()[0].links]

    # GIVEN a list of paths
    mocker.patch.object(ExternalDataAPI, "get_all_paths")
    ExternalDataAPI.get_all_paths.return_value = [fastq_file]

    mocker.patch.object(MockHousekeeperAPI, "last_version")
    MockHousekeeperAPI.last_version.return_value = None

    mocker.patch.object(MockHousekeeperAPI, "get_files")
    MockHousekeeperAPI.get_files.return_value = []

    # THEN none of the cases should exist in housekeeper
    assert all([external_data_api.housekeeper_api.bundle(sample) is None for sample in samples])

    # WHEN the sample bundles are added to housekeeper
    external_data_api.add_transfer_to_housekeeper(ticket_id=ticket_nr)

    # THEN the sample bundles exist in housekeeper and the file has been added to all bundles
    assert all([external_data_api.housekeeper_api.bundle(sample) is not None for sample in samples])
    assert all(
        [
            external_data_api.housekeeper_api.bundle(sample).versions[0].files[0].path
            == str(fastq_file.absolute())
            for sample in samples
        ]
    )


def test_checksum(fastq_file: Path):
    """Tests if the function correctly calculates md5sum and returns the correct result"""
    # GIVEN a fastq file with corresponding correct md5 file and a fastq file with a corresponding incorrect md5 file
    bad_md5sum_file_path: Path = fastq_file.parent.joinpath("fastq_run_R1_001.fastq.gz")

    # THEN a file with a correct md5 sum should return true
    assert check_md5sum(file_path=fastq_file, md5sum="a95cbb265540a2261fce941059784fd1")

    # THEN a file with an incorrect md5 sum should return false
    assert not check_md5sum(
        file_path=bad_md5sum_file_path, md5sum="c690b0124173772ec4cbbc43709d84ee"
    )


def test_extract_checksum(fastq_file: Path):
    """Tests if the function successfully extract the correct md5sum"""

    # Given a file containing an md5sum
    file = Path(str(fastq_file) + ".md5")

    # Then the function should extract it
    assert extract_md5sum(md5sum_file=file) == "a95cbb265540a2261fce941059784fd1"
