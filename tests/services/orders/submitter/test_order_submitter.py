import datetime as dt
from unittest.mock import patch

import pytest

from cg.clients.freshdesk.models import TicketResponse
from cg.exc import TicketCreationError
from cg.models.orders.constants import OrderType
from cg.services.orders.submitter.service import OrderSubmitter
from cg.services.orders.validation.errors.validation_errors import ValidationErrors
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.store.models import Case, Pool, Sample, User
from cg.store.store import Store


def monkeypatch_process_lims(monkeypatch: pytest.MonkeyPatch, order: Order) -> None:
    lims_project_data = {"id": "ADM1234", "date": dt.datetime.now()}
    if isinstance(order, OrderWithSamples):
        lims_map = {sample.name: f"ELH123A{index}" for index, sample in enumerate(order.samples)}
    elif isinstance(order, OrderWithCases):
        lims_map = {
            sample.name: f"ELH123A{case_index}-{sample_index}"
            for case_index, sample_index, sample in order.enumerated_new_samples
        }
    monkeypatch.setattr(
        "cg.services.orders.lims_service.service.OrderLimsService.process_lims",
        lambda *args, **kwargs: (lims_project_data, lims_map),
    )


def mock_freshdesk_ticket_creation(mock_create_ticket: callable, ticket_id: str):
    """Helper function to mock Freshdesk ticket creation."""
    mock_create_ticket.return_value = TicketResponse(
        id=int(ticket_id),
        description="This is a test description.",
        subject="Support needed..",
        status=2,
        priority=1,
    )


def mock_freshdesk_reply_to_ticket(mock_reply_to_ticket: callable):
    """Helper function to mock Freshdesk reply to ticket."""
    mock_reply_to_ticket.return_value = None


@pytest.mark.parametrize(
    "order_type, order_fixture",
    [
        (OrderType.BALSAMIC, "balsamic_order"),
        (OrderType.FASTQ, "fastq_order"),
        (OrderType.FLUFFY, "fluffy_order"),
        (OrderType.METAGENOME, "metagenome_order"),
        (OrderType.MICROBIAL_FASTQ, "microbial_fastq_order"),
        (OrderType.MICROSALT, "microsalt_order"),
        (OrderType.MIP_DNA, "mip_dna_order"),
        (OrderType.MIP_RNA, "mip_rna_order"),
        (OrderType.PACBIO_LONG_READ, "pacbio_order"),
        (OrderType.RML, "rml_order"),
        (OrderType.RNAFUSION, "rnafusion_order"),
        (OrderType.SARS_COV_2, "mutant_order"),
        (OrderType.TAXPROFILER, "taxprofiler_order"),
        (OrderType.TOMTE, "tomte_order"),
    ],
)
def test_submit_order(
    store_with_all_test_applications: Store,
    monkeypatch: pytest.MonkeyPatch,
    order_type: OrderType,
    order_fixture: str,
    order_submitter: OrderSubmitter,
    ticket_id: str,
    request: pytest.FixtureRequest,
):
    """Test submitting a valid order of each ordertype."""
    # GIVEN an order
    order: Order = request.getfixturevalue(order_fixture)

    # GIVEN a ticketing system that returns a ticket number
    with patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.create_ticket"
    ) as mock_create_ticket, patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.reply_to_ticket"
    ) as mock_reply_to_ticket:
        mock_freshdesk_ticket_creation(mock_create_ticket=mock_create_ticket, ticket_id=ticket_id)
        mock_freshdesk_reply_to_ticket(mock_reply_to_ticket)

        # GIVEN a mock LIMS that returns project data and sample name mapping
        monkeypatch_process_lims(monkeypatch=monkeypatch, order=order)

        # GIVEN a registered user
        user: User = store_with_all_test_applications._get_query(table=User).first()

        # GIVEN the dict representation of the order and a store without samples
        raw_order = order.model_dump(by_alias=True)
        assert not store_with_all_test_applications._get_query(table=Sample).first()

        # WHEN submitting the order
        result = order_submitter.submit(order_type=order_type, raw_order=raw_order, user=user)

        # THEN the result should contain the ticket number for the order
        for record in result["records"]:
            if isinstance(record, Pool):
                assert record.ticket == ticket_id
            elif isinstance(record, Sample):
                assert record.original_ticket == ticket_id
            elif isinstance(record, Case):
                for link_obj in record.links:
                    assert link_obj.sample.original_ticket == ticket_id


@pytest.mark.parametrize(
    "order_type, order_fixture",
    [
        (OrderType.MIP_DNA, "mip_dna_order"),
        (OrderType.MIP_RNA, "mip_rna_order"),
        (OrderType.BALSAMIC, "balsamic_order"),
    ],
)
def test_submit_ticketexception(
    order_submitter: OrderSubmitter,
    order_type: OrderType,
    order_fixture: str,
    request: pytest.FixtureRequest,
):

    # GIVEN an order
    order: OrderWithCases = request.getfixturevalue(order_fixture)
    raw_order = order.model_dump()
    raw_order["ticket_number"] = "#123456"
    raw_order["project_type"] = order_type

    # GIVEN a registered user
    user: User = order_submitter.validation_service.store._get_query(table=User).first()

    # GIVEN a mock Freshdesk ticket creation that raises TicketCreationError
    with patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.create_ticket",
        side_effect=TicketCreationError("ERROR"),
    ), patch(
        "cg.services.orders.validation.service.OrderValidationService._get_rule_validation_errors",
        return_value=ValidationErrors(),
    ):
        # GIVEN an order that does not have a name (ticket_nr)

        # WHEN the order is submitted and a TicketCreationError raised
        # THEN the TicketCreationError is not excepted
        with pytest.raises(TicketCreationError):
            order_submitter.submit(raw_order=raw_order, user=user, order_type=order_type)
