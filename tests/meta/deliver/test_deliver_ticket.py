"""Tests for the deliver ticket command"""

import logging
from pathlib import Path

from cg.constants.constants import Workflow
from cg.constants.delivery import INBOX_NAME
from cg.meta.deliver import DeliverTicketAPI
from cg.models.cg_config import CGConfig
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_get_inbox_path(
    cg_context: CGConfig, customer_id: str, helpers: StoreHelpers, mocker, ticket_id: str
):
    """Test to get the path to customer inbox on the HPC."""
    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN a case for analysis
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id="angrybird",
        name=ticket_id,
        data_analysis=Workflow.MUTANT,
    )

    mocker.patch.object(DeliverTicketAPI, "get_all_cases_from_ticket")
    DeliverTicketAPI.get_all_cases_from_ticket.return_value = [case]

    # WHEN running get_inbox_path
    inbox = deliver_ticket_api.get_inbox_path(ticket=ticket_id)

    # THEN a path is returned for cust000 with the folder ticket in the inbox
    assert inbox.parts[-3:] == (customer_id, INBOX_NAME, ticket_id)


def test_check_if_upload_is_needed(cg_context: CGConfig, mocker, ticket_id: str):
    """Test if upload is needed when it is needed"""
    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN the customer inbox
    mocker.patch.object(DeliverTicketAPI, "get_inbox_path")
    DeliverTicketAPI.get_inbox_path.return_value = Path(
        "th155h0uLdC3R7aNlyNo7eX157f0RsuReaNdIfiTd03St3n0Mg"
    )

    # WHEN running check_if_upload_is_needed
    is_upload_needed = deliver_ticket_api.check_if_upload_is_needed(ticket=ticket_id)

    # THEN it turns out that upload is needed
    assert is_upload_needed is True


def test_check_if_upload_is_needed_part_deux(cg_context: CGConfig, mocker, ticket_id: str):
    """Test if upload is needed when it is not needed"""
    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN the customer inbox
    mocker.patch.object(DeliverTicketAPI, "get_inbox_path")
    DeliverTicketAPI.get_inbox_path.return_value = Path("/")

    # WHEN running check_if_upload_is_needed
    is_upload_needed = deliver_ticket_api.check_if_upload_is_needed(ticket=ticket_id)

    # THEN it turns out that upload is not needed
    assert is_upload_needed is False


def test_get_samples_from_ticket(
    cg_context: CGConfig, mocker, helpers, analysis_store: Store, case_id, ticket_id: str
):
    """Test to get all samples from a ticket"""
    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN a case object
    case_obj = analysis_store.get_case_by_internal_id(internal_id=case_id)

    mocker.patch.object(DeliverTicketAPI, "get_all_cases_from_ticket")
    DeliverTicketAPI.get_all_cases_from_ticket.return_value = [case_obj]

    # WHEN checking which samples there are in the ticket
    all_samples: list = deliver_ticket_api.get_samples_from_ticket(ticket=ticket_id)

    # THEN concatenation is needed
    assert "child" in all_samples
    assert "father" in all_samples
    assert "mother" in all_samples


def test_all_samples_in_cust_inbox(
    cg_context: CGConfig, mocker, caplog, ticket_id: str, all_samples_in_inbox
):
    """Test that no samples will be reported as missing when all samples in inbox"""
    caplog.set_level(logging.INFO)

    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN a path to the customer inbox
    mocker.patch.object(DeliverTicketAPI, "get_inbox_path")
    DeliverTicketAPI.get_inbox_path.return_value = all_samples_in_inbox

    # GIVEN a ticket with certain samples
    mocker.patch.object(DeliverTicketAPI, "get_samples_from_ticket")
    DeliverTicketAPI.get_samples_from_ticket.return_value = ["ACC1", "ACC2"]

    # WHEN checking if a sample is missing
    deliver_ticket_api.report_missing_samples(ticket=ticket_id, dry_run=False)

    # THEN assert that all files were delivered
    assert "Data has been delivered for all samples" in caplog.text


def test_samples_missing_in_inbox(
    analysis_family: dict,
    cg_context: CGConfig,
    mocker,
    caplog,
    ticket_id: str,
    samples_missing_in_inbox,
):
    """Test when samples is missing in customer inbox."""
    caplog.set_level(logging.INFO)

    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN a path to the customer inbox
    mocker.patch.object(DeliverTicketAPI, "get_inbox_path")
    DeliverTicketAPI.get_inbox_path.return_value = samples_missing_in_inbox

    # GIVEN a ticket with certain samples
    mocker.patch.object(DeliverTicketAPI, "get_samples_from_ticket")
    DeliverTicketAPI.get_samples_from_ticket.return_value = [
        sample["name"] for sample in analysis_family["samples"]
    ]

    # WHEN checking if a sample is missing
    deliver_ticket_api.report_missing_samples(ticket=ticket_id, dry_run=False)

    # THEN assert that a sample that is not missing is not missing
    assert analysis_family["samples"][1]["name"] not in caplog.text

    # THEN assert that the empty case folder is not considered as a sample that is missing data
    assert analysis_family["name"] not in caplog.text

    # THEN assert that a missing sample is logged as missing
    assert analysis_family["samples"][0]["name"] in caplog.text
