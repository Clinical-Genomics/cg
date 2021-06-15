"""Tests for rsync API"""
import logging
import pytest
from pathlib import Path

from cgmodels.cg.constants import Pipeline
from cg.exc import CgError
from cg.meta.rsync import RsyncAPI
from cg.models.cg_config import CGConfig
from cg.store import Store


def test_get_source_path(
    cg_context: CGConfig, ticket_id: int, internal_id: str, mocker, helpers, analysis_store: Store
):
    """Test generating the source path before rsync"""

    # GIVEN an rsync API
    rsync_api = RsyncAPI(config=cg_context)

    # GIVEN a valid Sars-cov-2 case
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id=internal_id,
        case_id=ticket_id,
        data_analysis=Pipeline.SARS_COV_2,
    )

    # GIVEN file exists
    mocker.patch.object(RsyncAPI, "get_all_cases_from_ticket")
    RsyncAPI.get_all_cases_from_ticket.return_value = [case]

    # WHEN the source path is created
    source_path = rsync_api.get_source_path(ticket_id=ticket_id)

    # THEN the source path ends with a customer id, followed by "inbox" and a ticket id
    assert source_path.endswith(f"/cust000/inbox/{str(ticket_id)}/")


def test_get_source_path_no_case(cg_context: CGConfig, ticket_id: int, mocker, helpers, caplog):
    """Test generating the source path before rsync when there is no case"""
    caplog.set_level(logging.WARNING)

    # GIVEN an rsync API
    rsync_api = RsyncAPI(config=cg_context)

    # GIVEN file exists
    mocker.patch.object(RsyncAPI, "get_all_cases_from_ticket")
    RsyncAPI.get_all_cases_from_ticket.return_value = None

    with pytest.raises(CgError):
        # WHEN the source path is collected
        rsync_api.get_source_path(ticket_id=ticket_id)

        # THEN the source path ends with a customer id, followed by "inbox" and a ticket id
        assert "Could not find any cases for ticket_id" in caplog.text


def test_get_destination_path(
    cg_context: CGConfig, ticket_id: int, internal_id: str, helpers, mocker
):
    """Test generating the destination path before rsync"""
    # GIVEN an rsync API
    rsync_api = RsyncAPI(config=cg_context)

    # GIVEN a valid Sars-cov-2 case
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id=internal_id,
        case_id=ticket_id,
        data_analysis=Pipeline.SARS_COV_2,
    )

    # GIVEN file exists
    mocker.patch.object(RsyncAPI, "get_all_cases_from_ticket")
    RsyncAPI.get_all_cases_from_ticket.return_value = [case]

    # WHEN the destination path is created
    destination_path = rsync_api.get_destination_path(ticket_id=ticket_id)

    # THEN the destination path is in the format server.name.se:/path/cust_id/path/ticket_id/
    assert destination_path == f"server.name.se:/some/cust000/inbox/{str(ticket_id)}/"


def test_set_log_dir(cg_context: CGConfig, ticket_id: int, caplog):
    """Test function to set log dir for path"""

    caplog.set_level(logging.INFO)

    # GIVEN an RsyncAPI, with its base path as its log dir
    rsync_api: RsyncAPI = RsyncAPI(config=cg_context)
    base_path = rsync_api.log_dir

    # WHEN setting the log directory
    rsync_api.set_log_dir(ticket_id=ticket_id)

    # THEN the log dir should set to a new path, different from the base path
    assert base_path.as_posix() != rsync_api.log_dir.as_posix()
    assert "Setting log dir to:" in caplog.text


def test_make_log_dir(cg_context: CGConfig, ticket_id: int, caplog):
    """Test generating the directory for logging"""
    caplog.set_level(logging.INFO)

    # GIVEN an rsync API
    rsync_api = RsyncAPI(config=cg_context)

    # WHEN the log directory is created
    rsync_api.set_log_dir(ticket_id=ticket_id)
    rsync_api.create_log_dir(dry_run=True)

    # THEN the path is not created since it is a dry run
    assert "Would have created path" in caplog.text

    # THEN the created path is
    assert str(rsync_api.log_dir).startswith(f"/another/path/{str(ticket_id)}")


def test_run_rsync_on_slurm(
    cg_context: CGConfig, ticket_id: int, internal_id: str, caplog, mocker, helpers
):
    """Test for running rsync on slurm"""
    caplog.set_level(logging.INFO)

    # GIVEN an rsync API
    rsync_api = RsyncAPI(config=cg_context)

    # GIVEN a valid Sars-cov-2 case
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id=internal_id,
        case_id=ticket_id,
        data_analysis=Pipeline.MICROSALT,
    )

    # GIVEN paths needed to run rsync
    mocker.patch.object(RsyncAPI, "get_source_path")
    RsyncAPI.get_source_path.return_value = Path("/path/to/source")

    mocker.patch.object(RsyncAPI, "get_destination_path")
    RsyncAPI.get_destination_path.return_value = Path("/path/to/destination")

    mocker.patch.object(RsyncAPI, "get_all_cases_from_ticket")
    RsyncAPI.get_all_cases_from_ticket.return_value = [case]

    # WHEN the destination path is created
    sbatch_number = rsync_api.run_rsync_on_slurm(ticket_id=ticket_id, dry_run=True)

    # THEN check that SARS-COV-2 analysis is not delivered
    assert "Delivering report for SARS-COV-2 analysis" not in caplog.text

    # THEN check that an integer was returned as sbatch number
    assert isinstance(sbatch_number, int)
