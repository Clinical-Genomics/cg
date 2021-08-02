"""Tests for the transfer of external data"""
import logging
from pathlib import Path
import os

from tests.cli.workflow.mip.conftest import fixture_dna_mip_context
from tests.cli.workflow.mip.conftest import fixture_mip_case_ids
from tests.cli.workflow.mip.conftest import fixture_mip_case_id
from tests.apps.mip.conftest import tb_api
from cg.meta.orders.external_data import ExternalDataAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models


def test_create_log_dir(caplog, external_data_api: ExternalDataAPI):
    """Test generating the directory for logging"""
    caplog.set_level(logging.INFO)

    # WHEN the log directory is created
    log_dir = external_data_api.create_log_dir(ticket_id=999999, dry_run=True)

    # THEN the path is not created since it is a dry run
    assert "Would have created path" in caplog.text

    # THEN the created path is
    assert str(log_dir).startswith("/another/path/999999")


def test_create_source_path(external_data_api: ExternalDataAPI):
    """Test generating the source path"""

    # WHEN the source path is created
    source_path = external_data_api.create_source_path(
        ticket_id=999999, raw_path="/path/%s", cust_sample_id="ABC123", cust_id="cust000"
    )

    # THEN the source path is
    assert source_path == "/path/cust000/999999/ABC123/"


def test_create_destination_path(external_data_api: ExternalDataAPI):
    """Test generating the destination path"""

    # WHEN the source path is created
    destination_path = external_data_api.create_destination_path(
        raw_path="/path/%s", lims_sample_id="ACC123", cust_id="cust000"
    )

    # THEN the source path is
    assert destination_path == "/path/cust000/ACC123/"


def test_download_sample(external_data_api: ExternalDataAPI, mocker):
    """Test for downloading external data via slurm"""

    # GIVEN paths needed to run rsync
    mocker.patch.object(ExternalDataAPI, "create_log_dir")
    ExternalDataAPI.create_log_dir.return_value = Path("/path/to/log")

    mocker.patch.object(ExternalDataAPI, "create_source_path")
    ExternalDataAPI.create_source_path.return_value = Path("/path/to/source")

    mocker.patch.object(ExternalDataAPI, "create_destination_path")
    ExternalDataAPI.create_destination_path.return_value = Path("/path/to/destination")

    # WHEN the destination path is created
    sbatch_number = external_data_api.download_sample(
        cust_id="cust000",
        ticket_id=123456,
        cust_sample_id="ABC123",
        lims_sample_id="ACC123",
        dry_run=True,
    )

    # THEN check that an integer was returned as sbatch number
    assert isinstance(sbatch_number, int)


def test_get_all_fastq(
    cg_context: CGConfig, external_data_directory, external_data_api: ExternalDataAPI
):
    """Test the finding of fastq.gz files in customer directories."""
    for folder in os.listdir(external_data_directory):
        # WHEN the list of file-paths is created
        files = external_data_api.get_all_fastq(
            sample_folder=str(external_data_directory) + "/" + folder
        )
        # THEN only fast.gz files are returned
        assert [tmp.endswith("fastq.gz") for tmp in files]


def test_configure_housekeeper(
    external_data_api: ExternalDataAPI,
    caplog,
    mocker,
    case_id,
    ticket_nr,
    dna_mip_context,
):
    caplog.set_level(logging.INFO)
    """Test the finding of fastq.gz files in customer directories."""

    # GIVEN a case to analyze
    mip_api = dna_mip_context.meta_apis["analysis_api"]
    cases = mip_api.status_db.query(models.Family).filter(models.Family.internal_id == case_id)

    # GIVEN a case is available for analysis
    mocker.patch.object(Store, "get_cases_from_ticket")
    Store.get_cases_from_ticket.return_value = cases

    # GIVEN a list of paths
    mocker.patch.object(ExternalDataAPI, "get_all_paths")
    ExternalDataAPI.get_all_paths.return_value = ["/path/to/something/"]

    # WHEN files are added to housekeeper
    external_data_api.configure_housekeeper(ticket_id=ticket_nr, dry_run=True)

    # THEN it is announced that files would have been added
    assert "Would have" in caplog.text
