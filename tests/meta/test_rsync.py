"""Tests for rsync API"""
import logging
import pytest

from cgmodels.cg.constants import Pipeline

from cg.exc import CgError
from cg.meta.rsync import RsyncAPI
from cg.models.cg_config import CGConfig
from cg.store import Store


def test_get_source_path(cg_context: CGConfig, mocker, helpers, analysis_store: Store):
    """Test generating the source path before rsync"""

    # GIVEN an rsync API
    rsync_api = RsyncAPI(config=cg_context)

    # GIVEN a valid Sars-cov-2 case
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id="angrybird",
        case_id=999999,
        data_analysis=Pipeline.SARS_COV_2,
    )

    # GIVEN file exists
    mocker.patch.object(RsyncAPI, "get_all_cases_from_ticket")
    RsyncAPI.get_all_cases_from_ticket.return_value = [case]

    # WHEN the source path is created
    source_path = rsync_api.get_source_path(ticket_id=999999)

    # THEN the source path ends with a customer id, followed by "inbox" and a ticket id
    assert source_path.endswith("/cust000/inbox/999999/")


def test_get_source_path_no_case(cg_context: CGConfig, mocker, helpers, caplog):
    """Test generating the source path before rsync when there is no case"""
    caplog.set_level(logging.WARNING)

    # GIVEN an rsync API
    rsync_api = RsyncAPI(config=cg_context)

    # GIVEN file exists
    mocker.patch.object(RsyncAPI, "get_all_cases_from_ticket")
    RsyncAPI.get_all_cases_from_ticket.return_value = None

    with pytest.raises(CgError):
        # WHEN the source path is collected
        rsync_api.get_source_path(ticket_id=999999)

        # THEN the source path ends with a customer id, followed by "inbox" and a ticket id
        assert "Could not find any cases for ticket_id" in caplog.text


def test_get_destination_path(cg_context: CGConfig, helpers, mocker):
    """Test generating the destination path before rsync"""
    # GIVEN an rsync API
    rsync_api = RsyncAPI(config=cg_context)

    # GIVEN a valid Sars-cov-2 case
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id="angrybird",
        case_id=999999,
        data_analysis=Pipeline.SARS_COV_2,
    )

    # GIVEN file exists
    mocker.patch.object(RsyncAPI, "get_all_cases_from_ticket")
    RsyncAPI.get_all_cases_from_ticket.return_value = [case]

    # WHEN the destination path is created
    destination_path = rsync_api.get_destination_path(ticket_id=999999)

    # THEN the destination path is in the format server.name.se:/path/cust_id/path/ticket_id/
    assert destination_path == "server.name.se:/some/cust000/path/999999/"


def test_create_log_dir(cg_context: CGConfig, caplog):
    """Test generating the directory for logging"""
    caplog.set_level(logging.INFO)

    # GIVEN an rsync API
    rsync_api = RsyncAPI(config=cg_context)

    # WHEN the log directory is created
    log_dir = rsync_api.create_log_dir(ticket_id=999999, dry_run=True)

    # THEN the path is not created since it is a dry run
    assert "Would have created path" in caplog.text

    # THEN the created path is
    assert str(log_dir).startswith("/another/path/999999")
