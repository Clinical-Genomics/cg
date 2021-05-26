"""Tests for the deliver ticket command"""
from pathlib import Path

from cg.meta.deliver_ticket import DeliverTicketAPI
from cg.models.cg_config import CGConfig
from cgmodels.cg.constants import Pipeline
from cg.store import Store


def test_get_inbox_path(cg_context: CGConfig, helpers, mocker):
    """Test to get the path to customer inbox on hasta"""
    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN a case for analysis
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id="angrybird",
        case_id=123456,
        data_analysis=Pipeline.SARS_COV_2,
    )

    mocker.patch.object(DeliverTicketAPI, "get_all_cases_from_ticket")
    DeliverTicketAPI.get_all_cases_from_ticket.return_value = [case]

    # WHEN running get_inbox_path
    inbox = deliver_ticket_api.get_inbox_path(ticket_id=123456)

    # THEN a path is returned for cust000 with the folder 123456 in the inbox
    assert str(inbox).endswith("/cust000/inbox/123456")


def test_check_if_upload_is_needed(cg_context: CGConfig, mocker):
    """Test if upload is needed when it is needed"""
    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN the customer inbox
    mocker.patch.object(DeliverTicketAPI, "get_inbox_path")
    DeliverTicketAPI.get_inbox_path.return_value = Path(
        "th155h0uLdC3R7aNlyNo7eX157f0RsuReaNdIfiTd03St3n0Mg"
    )

    # WHEN running check_if_upload_is_needed
    is_upload_needed = deliver_ticket_api.check_if_upload_is_needed(ticket_id=123456)

    # THEN it turns out that upload is needed
    assert is_upload_needed is True


def test_check_if_upload_is_needed_part_deux(cg_context: CGConfig, mocker):
    """Test if upload is needed when it is not needed"""
    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN the customer inbox
    mocker.patch.object(DeliverTicketAPI, "get_inbox_path")
    DeliverTicketAPI.get_inbox_path.return_value = Path("/")

    # WHEN running check_if_upload_is_needed
    is_upload_needed = deliver_ticket_api.check_if_upload_is_needed(ticket_id=123456)

    # THEN it turns out that upload is not needed
    assert is_upload_needed is False


def test_generate_date_tag(cg_context: CGConfig, mocker, helpers, timestamp_today):
    """Test to generate the date tag"""
    # GIVEN a deliver_ticket API
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)

    # GIVEN a case for analysis
    case = helpers.add_case(
        store=cg_context.status_db,
        internal_id="angrybird",
        case_id=123456,
        data_analysis=Pipeline.SARS_COV_2,
    )

    case.ordered_at = timestamp_today

    mocker.patch.object(DeliverTicketAPI, "get_all_cases_from_ticket")
    DeliverTicketAPI.get_all_cases_from_ticket.return_value = [case]

    # WHEN running generate_date_tag
    date = deliver_ticket_api.generate_date_tag(ticket_id=123456)

    # THEN check that a date was returned
    assert str(timestamp_today) == str(date)


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
    cg_context: CGConfig, mocker, helpers, analysis_store: Store, case_id, ticket_nr
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
    is_concatenation_needed = deliver_ticket_api.check_if_concatenation_is_needed(
        ticket_id=ticket_nr
    )

    # THEN concatenation is not needed
    assert is_concatenation_needed is False


def test_check_if_concatenation_is_needed_part_deux(
    cg_context: CGConfig, mocker, helpers, analysis_store: Store, case_id, ticket_nr
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
    is_concatenation_needed = deliver_ticket_api.check_if_concatenation_is_needed(
        ticket_id=ticket_nr
    )

    # THEN concatenation is needed
    assert is_concatenation_needed is True
