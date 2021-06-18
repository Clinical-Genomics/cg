"""Tests for rsync API"""
import logging
import pytest
from pathlib import Path

from cgmodels.cg.constants import Pipeline
from cg.exc import CgError
from cg.meta.rsync import RsyncAPI
from cg.models.cg_config import CGConfig
from cg.store import models


def test_get_source_and_destination_paths(
    mutant_case: models.Family, rsync_api: RsyncAPI, ticket_number: int, mocker
):
    """Test generating the source path before rsync"""

    # GIVEN a valid Sars-cov-2 case
    case = mutant_case

    # GIVEN file exists
    mocker.patch.object(RsyncAPI, "get_all_cases_from_ticket")
    RsyncAPI.get_all_cases_from_ticket.return_value = [case]

    # WHEN the source path is created
    source_and_destination_paths = rsync_api.get_source_and_destination_paths(
        ticket_id=ticket_number
    )

    # THEN the source path ends with a customer id, followed by "inbox" and a ticket id
    assert source_and_destination_paths["delivery_source_path"].endswith(
        f"/cust000/inbox/{str(ticket_number)}/"
    )
    # THEN the destination path is in the format server.name.se:/path/cust_id/path/ticket_id/
    assert (
        source_and_destination_paths["rsync_destination_path"]
        == f"server.name.se:/some/cust000/inbox/{str(ticket_number)}/"
    )


def test_get_source_path_no_case(rsync_api: RsyncAPI, ticket_number: int, mocker, helpers, caplog):
    """Test generating the source path before rsync when there is no case"""
    caplog.set_level(logging.WARNING)

    # GIVEN file exists
    mocker.patch.object(RsyncAPI, "get_all_cases_from_ticket")
    RsyncAPI.get_all_cases_from_ticket.return_value = None

    with pytest.raises(CgError):
        # WHEN the source path is collected
        rsync_api.get_source_and_destination_paths(ticket_id=ticket_number)

        # THEN the source path ends with a customer id, followed by "inbox" and a ticket id
        assert "Could not find any cases for ticket_id" in caplog.text


def test_set_log_dir(rsync_api: RsyncAPI, ticket_number: int, caplog):
    """Test function to set log dir for path"""

    caplog.set_level(logging.INFO)

    # GIVEN an RsyncAPI, with its base path as its log dir
    base_path: Path = rsync_api.log_dir

    # WHEN setting the log directory
    rsync_api.set_log_dir(ticket_id=ticket_number)

    # THEN the log dir should set to a new path, different from the base path
    assert base_path.as_posix() != rsync_api.log_dir.as_posix()
    assert "Setting log dir to:" in caplog.text


def test_make_log_dir(rsync_api: RsyncAPI, ticket_number: int, caplog):
    """Test generating the directory for logging"""
    caplog.set_level(logging.INFO)

    # WHEN the log directory is created
    rsync_api.set_log_dir(ticket_id=ticket_number)
    rsync_api.create_log_dir(dry_run=True)

    # THEN the path is not created since it is a dry run
    assert "Would have created path" in caplog.text

    # THEN the created path is
    assert str(rsync_api.log_dir).startswith(f"/another/path/{str(ticket_number)}")


def test_run_rsync_on_slurm(
    microsalt_case: models.Family, rsync_api: RsyncAPI, ticket_number: int, caplog, mocker, helpers
):
    """Test for running rsync on slurm"""
    caplog.set_level(logging.INFO)

    # GIVEN a valid microsalt case
    case: models.Family = microsalt_case

    # GIVEN paths needed to run rsync
    mocker.patch.object(RsyncAPI, "get_source_and_destination_paths")
    RsyncAPI.get_source_and_destination_paths.return_value = {
        "delivery_source_path": Path("/path/to/source"),
        "rsync_destination_path": Path("/path/to/destination"),
    }

    mocker.patch.object(RsyncAPI, "get_all_cases_from_ticket")
    RsyncAPI.get_all_cases_from_ticket.return_value = [case]

    # WHEN the destination path is created
    sbatch_number: int = rsync_api.run_rsync_on_slurm(ticket_id=ticket_number, dry_run=True)

    # THEN check that SARS-COV-2 analysis is not delivered
    assert "Delivering report for SARS-COV-2 analysis" not in caplog.text

    # THEN check that an integer was returned as sbatch number
    assert isinstance(sbatch_number, int)
