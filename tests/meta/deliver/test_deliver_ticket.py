"""Tests for the deliver ticket command"""
import logging
from pathlib import Path

from cg.constants.delivery import INBOX_NAME
from cg.meta.deliver_ticket import DeliverTicketAPI
from cg.models.cg_config import CGConfig
from cgmodels.cg.constants import Pipeline
from cg.store import Store
from tests.store_helpers import StoreHelpers


def test_get_inbox_path(
    cg_context: CGConfig, customer_id: str, helpers: StoreHelpers, mocker, ticket: str
):
    """Test to get the path to customer inbox on the HPC."""
    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN a case for analysis
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id="angrybird",
        name=ticket,
        data_analysis=Pipeline.SARS_COV_2,
    )

    mocker.patch.object(DeliverTicketAPI, "get_all_cases_from_ticket")
    DeliverTicketAPI.get_all_cases_from_ticket.return_value = [case]

    # WHEN running get_inbox_path
    inbox = deliver_ticket_api.get_inbox_path(ticket=ticket)

    # THEN a path is returned for cust000 with the folder ticket in the inbox
    assert inbox.parts[-3:] == (customer_id, INBOX_NAME, ticket)


def test_check_if_upload_is_needed(cg_context: CGConfig, mocker, ticket: str):
    """Test if upload is needed when it is needed"""
    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN the customer inbox
    mocker.patch.object(DeliverTicketAPI, "get_inbox_path")
    DeliverTicketAPI.get_inbox_path.return_value = Path(
        "th155h0uLdC3R7aNlyNo7eX157f0RsuReaNdIfiTd03St3n0Mg"
    )

    # WHEN running check_if_upload_is_needed
    is_upload_needed = deliver_ticket_api.check_if_upload_is_needed(ticket=ticket)

    # THEN it turns out that upload is needed
    assert is_upload_needed is True


def test_check_if_upload_is_needed_part_deux(cg_context: CGConfig, mocker, ticket: str):
    """Test if upload is needed when it is not needed"""
    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN the customer inbox
    mocker.patch.object(DeliverTicketAPI, "get_inbox_path")
    DeliverTicketAPI.get_inbox_path.return_value = Path("/")

    # WHEN running check_if_upload_is_needed
    is_upload_needed = deliver_ticket_api.check_if_upload_is_needed(ticket=ticket)

    # THEN it turns out that upload is not needed
    assert is_upload_needed is False


def test_generate_date_tag(cg_context: CGConfig, mocker, helpers, ticket: str, timestamp_now):
    """Test to generate the date tag."""
    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN a case for analysis
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id="angrybird",
        name=ticket,
        data_analysis=Pipeline.SARS_COV_2,
    )

    case.ordered_at = timestamp_now

    mocker.patch.object(DeliverTicketAPI, "get_all_cases_from_ticket")
    DeliverTicketAPI.get_all_cases_from_ticket.return_value = [case]

    # WHEN running generate_date_tag
    date = deliver_ticket_api.generate_date_tag(ticket=ticket)

    # THEN check that a date was returned
    assert str(timestamp_now) == str(date)


def test_sort_files(cg_context: CGConfig):
    """Test to sort files"""
    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN a list of paths
    unsorted_list_of_paths = []
    unsorted_list_of_paths.append(Path("2.fastq"))
    unsorted_list_of_paths.append(Path("1.fastq"))
    unsorted_list_of_paths.append(Path("3.fastq"))

    # WHEN when sorting the paths
    sorted_list_of_paths = deliver_ticket_api.sort_files(unsorted_list_of_paths)

    # THEN 1.fastq is first in the list
    assert str(sorted_list_of_paths[0]) == "1.fastq"


def test_check_if_concatenation_is_needed(
    cg_context: CGConfig, mocker, helpers, analysis_store: Store, case_id, ticket: str
):
    """Test to check if concatenation is needed when it is not needed"""
    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN a case object
    case_obj = analysis_store.family(case_id)

    mocker.patch.object(DeliverTicketAPI, "get_all_cases_from_ticket")
    DeliverTicketAPI.get_all_cases_from_ticket.return_value = [case_obj]

    # GIVEN an application tag that is not a micro application
    mocker.patch.object(DeliverTicketAPI, "get_app_tag")
    DeliverTicketAPI.get_app_tag.return_value = "RMLP15S175"

    # WHEN running check_if_concatenation_is_needed
    is_concatenation_needed = deliver_ticket_api.check_if_concatenation_is_needed(ticket=ticket)

    # THEN concatenation is not needed
    assert is_concatenation_needed is False


def test_check_if_concatenation_is_needed_part_deux(
    cg_context: CGConfig, mocker, helpers, analysis_store: Store, case_id, ticket: str
):
    """Test to check if concatenation is needed when it is needed"""
    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN a case object
    case_obj = analysis_store.family(case_id)

    mocker.patch.object(DeliverTicketAPI, "get_all_cases_from_ticket")
    DeliverTicketAPI.get_all_cases_from_ticket.return_value = [case_obj]

    # GIVEN an application tag that is a micro application
    mocker.patch.object(DeliverTicketAPI, "get_app_tag")
    DeliverTicketAPI.get_app_tag.return_value = "MWRNXTR003"

    # WHEN running check_if_concatenation_is_needed
    is_concatenation_needed = deliver_ticket_api.check_if_concatenation_is_needed(ticket=ticket)

    # THEN concatenation is needed
    assert is_concatenation_needed is True


def test_get_all_samples_from_ticket(
    cg_context: CGConfig, mocker, helpers, analysis_store: Store, case_id, ticket: str
):
    """Test to get all samples from a ticket"""
    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN a case object
    case_obj = analysis_store.family(case_id)

    mocker.patch.object(DeliverTicketAPI, "get_all_cases_from_ticket")
    DeliverTicketAPI.get_all_cases_from_ticket.return_value = [case_obj]

    # WHEN checking which samples there are in the ticket
    all_samples = deliver_ticket_api.get_all_samples_from_ticket(ticket=ticket)

    # THEN concatenation is needed
    assert "child" in all_samples
    assert "father" in all_samples
    assert "mother" in all_samples


def test_all_samples_in_cust_inbox(
    cg_context: CGConfig, mocker, caplog, ticket: str, all_samples_in_inbox
):
    """Test that no samples will be reported as missing when all samples in inbox"""
    caplog.set_level(logging.INFO)

    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN a path to the customer inbox
    mocker.patch.object(DeliverTicketAPI, "get_inbox_path")
    DeliverTicketAPI.get_inbox_path.return_value = all_samples_in_inbox

    # GIVEN a ticket with certain samples
    mocker.patch.object(DeliverTicketAPI, "get_all_samples_from_ticket")
    DeliverTicketAPI.get_all_samples_from_ticket.return_value = ["ACC1", "ACC2"]

    # WHEN checking if a sample is missing
    deliver_ticket_api.report_missing_samples(ticket=ticket, dry_run=False)

    # THEN assert that all files were delivered
    assert "Data has been delivered for all samples" in caplog.text


def test_samples_missing_in_inbox(
    analysis_family: dict,
    cg_context: CGConfig,
    mocker,
    caplog,
    ticket: str,
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
    mocker.patch.object(DeliverTicketAPI, "get_all_samples_from_ticket")
    DeliverTicketAPI.get_all_samples_from_ticket.return_value = [
        sample["name"] for sample in analysis_family["samples"]
    ]

    # WHEN checking if a sample is missing
    deliver_ticket_api.report_missing_samples(ticket=ticket, dry_run=False)

    # THEN assert that a sample that is not missing is not missing
    assert analysis_family["samples"][1]["name"] not in caplog.text

    # THEN assert that the empty case folder is not considered as a sample that is missing data
    assert analysis_family["name"] not in caplog.text

    # THEN assert that a missing sample is logged as missing
    assert analysis_family["samples"][0]["name"] in caplog.text
