"""Tests for the transfer of external data"""
import logging
from pathlib import Path

from cgmodels.cg.constants import Pipeline
from cg.meta.orders.external_data import ExternalDataAPI
from cg.models.cg_config import CGConfig


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
    """Test for running rsync on slurm"""

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
