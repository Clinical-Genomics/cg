import datetime as dt
from unittest.mock import patch

import pytest

from cg.clients.freshdesk.models import TicketResponse
from cg.constants import DataDelivery
from cg.constants.constants import Workflow
from cg.exc import OrderError, TicketCreationError
from cg.meta.orders import OrdersAPI
from cg.models.orders.order import OrderIn, OrderType
from cg.models.orders.sample_base import StatusEnum
from cg.services.order_validation_service.errors.validation_errors import ValidationErrors
from cg.services.order_validation_service.models.existing_sample import ExistingSample
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.models.order_with_samples import OrderWithSamples
from cg.services.order_validation_service.workflows.balsamic.models.order import BalsamicOrder
from cg.services.order_validation_service.workflows.mip_dna.models.order import MipDnaOrder
from cg.services.order_validation_service.workflows.mip_rna.models.order import MipRnaOrder
from cg.store.models import Case, Customer, Pool, Sample, User
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def monkeypatch_process_lims(monkeypatch, order: Order) -> None:
    lims_project_data = {"id": "ADM1234", "date": dt.datetime.now()}
    if isinstance(order, OrderWithSamples):
        lims_map = {sample.name: f"ELH123A{index}" for index, sample in enumerate(order.samples)}
    elif isinstance(order, OrderWithCases):
        lims_map = {
            sample.name: f"ELH123A{case_index}-{sample_index}"
            for case_index, sample_index, sample in order.enumerated_new_samples
        }
    monkeypatch.setattr(
        "cg.services.orders.order_lims_service.order_lims_service.OrderLimsService.process_lims",
        lambda *args, **kwargs: (lims_project_data, lims_map),
    )


def mock_freshdesk_ticket_creation(mock_create_ticket, ticket_id: str):
    """Helper function to mock Freshdesk ticket creation."""
    mock_create_ticket.return_value = TicketResponse(
        id=int(ticket_id),
        description="This is a test description.",
        subject="Support needed..",
        status=2,
        priority=1,
    )


def mock_freshdesk_reply_to_ticket(mock_reply_to_ticket):
    """Helper function to mock Freshdesk reply to ticket."""
    mock_reply_to_ticket.return_value = None


def test_too_long_order_name():
    # GIVEN order with more than allowed characters name
    long_name = "A super long order name that is longer than sixty-four characters."
    assert len(long_name) > Sample.order.property.columns[0].type.length

    # WHEN placing it in the pydantic order model
    # THEN an error is raised
    with pytest.raises(ValueError):
        OrderIn(name=long_name, customer="", comment="", samples=[])


@pytest.mark.parametrize(
    "order_type",
    [
        OrderType.BALSAMIC,
        OrderType.FASTQ,
        OrderType.FLUFFY,
        OrderType.METAGENOME,
        # OrderType.MICROBIAL_FASTQ,
        # OrderType.MICROSALT,
        # OrderType.MIP_DNA,
        # OrderType.MIP_RNA,
        # OrderType.PACBIO_LONG_READ,
        # OrderType.RML,
        # OrderType.RNAFUSION,
        # OrderType.SARS_COV_2,
        # OrderType.TAXPROFILER,
        # OrderType.TOMTE,
    ],
)
def test_submit_order(
    all_orders_to_submit: dict,
    store_with_all_test_applications: Store,
    monkeypatch: pytest.MonkeyPatch,
    order_type: OrderType,
    orders_api: OrdersAPI,
    ticket_id: str,
    email_address: str,
    helpers: StoreHelpers,
):
    # GIVEN an order
    order: Order = all_orders_to_submit[order_type]

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

        # GIVEN a raw order and an empty store
        raw_order = order.model_dump(by_alias=True)
        assert not store_with_all_test_applications._get_query(table=Sample).first()

        # WHEN submitting the order

        result = orders_api.submit(order_type=order_type, raw_order=raw_order, user=user)

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
    "order_type, order_name",
    [
        (OrderType.MIP_DNA, "mip_dna_order"),
        (OrderType.MIP_RNA, "mip_rna_order"),
        (OrderType.BALSAMIC, "balsamic_order"),
    ],
)
def test_submit_ticketexception(
    mip_dna_order: MipDnaOrder,
    mip_rna_order: MipRnaOrder,
    balsamic_order: BalsamicOrder,
    orders_api: OrdersAPI,
    order_type: OrderType,
    order_name: str,
    helpers: StoreHelpers,
):

    # GIVEN an order
    order: OrderWithCases = locals().get(order_name)
    raw_order = order.model_dump()
    raw_order["ticket_number"] = "#123456"
    raw_order["project_type"] = order_type
    customer = helpers.ensure_customer(store=orders_api.validation_service.store)
    user = helpers.ensure_user(store=orders_api.validation_service.store, customer=customer)

    # GIVEN a mock Freshdesk ticket creation that raises TicketCreationError
    with patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.create_ticket",
        side_effect=TicketCreationError("ERROR"),
    ), patch(
        "cg.services.order_validation_service.order_validation_service.OrderValidationService._get_rule_validation_errors",
        return_value=ValidationErrors(),
    ):
        # GIVEN an order that does not have a name (ticket_nr)

        # WHEN the order is submitted and a TicketCreationError raised
        # THEN the TicketCreationError is not excepted
        with pytest.raises(TicketCreationError):
            orders_api.submit(raw_order=raw_order, user=user, order_type=order_type)


@pytest.mark.xfail(reason="Change in order validation")
@pytest.mark.parametrize(
    "order_type",
    [OrderType.MIP_DNA, OrderType.MIP_RNA, OrderType.BALSAMIC],
)
def test_submit_illegal_sample_customer(
    all_orders_to_submit: dict,
    monkeypatch: pytest.MonkeyPatch,
    order_type: OrderType,
    orders_api: OrdersAPI,
    sample_store: Store,
    user_mail: str,
    user_name: str,
    helpers: StoreHelpers,
):
    order_data: OrderWithCases = all_orders_to_submit[order_type]
    for _, _, sample in order_data.enumerated_new_samples:
        helpers.ensure_application_version(store=sample_store, application_tag=sample.application)
    monkeypatch_process_lims(monkeypatch, order_data)
    old_customer: Customer = sample_store.get_customers()[0]
    # GIVEN we have an order with a customer that is not in the same customer group as customer
    # that the samples originate from
    new_customer = sample_store.add_customer(
        "customer999",
        "customer 999",
        scout_access=True,
        invoice_address="dummy street",
        invoice_reference="dummy nr",
    )
    sample_store.session.add(new_customer)
    existing_db_sample: Sample = sample_store._get_query(table=Sample).first()
    existing_db_sample.customer = new_customer
    sample_store.session.add(existing_db_sample)
    sample_store.session.commit()
    existing_order_sample = ExistingSample(
        internal_id=existing_db_sample.internal_id, status=StatusEnum.affected
    )
    order_data.cases[0].samples.append(existing_order_sample)
    user = sample_store.add_user(customer=old_customer, email=user_mail, name=user_name)

    # WHEN calling submit
    # THEN an OrderError should be raised on illegal customer
    with pytest.raises(OrderError):
        orders_api.submit(
            raw_order=order_data.model_dump(by_alias=True), user=user, order_type=order_type
        )


@pytest.mark.xfail(reason="Change in order validation")
@pytest.mark.parametrize(
    "order_type",
    [OrderType.MIP_DNA, OrderType.MIP_RNA, OrderType.BALSAMIC],
)
def test_submit_scout_legal_sample_customer(
    all_orders_to_submit: dict,
    monkeypatch: pytest.MonkeyPatch,
    order_type: OrderType,
    orders_api: OrdersAPI,
    sample_store: Store,
    user_mail: str,
    user_name: str,
    ticket_id: str,
    helpers: StoreHelpers,
):
    with patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.create_ticket"
    ) as mock_create_ticket, patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.reply_to_ticket"
    ) as mock_reply_to_ticket:
        old_customer: Customer = sample_store.get_customers()[0]
        mock_freshdesk_ticket_creation(mock_create_ticket, ticket_id)
        mock_freshdesk_reply_to_ticket(mock_reply_to_ticket)
        order_data: OrderWithCases = all_orders_to_submit[order_type]
        for _, _, sample in order_data.enumerated_new_samples:
            helpers.ensure_application_version(
                store=sample_store, application_tag=sample.application
            )
        monkeypatch_process_lims(monkeypatch, order_data)
        # GIVEN we have an order with a customer that is in the same customer group as customer
        # that the samples originate from
        collaboration = sample_store.add_collaboration("customer999only", "customer 999 only group")
        sample_store.session.add(collaboration)
        sample_customer = sample_store.add_customer(
            "customer1",
            "customer 1",
            scout_access=True,
            invoice_address="dummy street 1",
            invoice_reference="dummy nr",
        )
        order_customer = sample_store.add_customer(
            "customer2",
            "customer 2",
            scout_access=True,
            invoice_address="dummy street 2",
            invoice_reference="dummy nr",
        )
        sample_customer.collaborations.append(collaboration)
        order_customer.collaborations.append(collaboration)
        sample_store.session.add(sample_customer)
        sample_store.session.add(order_customer)
        existing_db_sample: Sample = sample_store._get_query(table=Sample).first()
        existing_db_sample.customer = sample_customer
        sample_store.session.commit()
        order_data.customer = order_customer.internal_id

        existing_order_sample = ExistingSample(
            internal_id=existing_db_sample.internal_id, status=StatusEnum.affected
        )
        order_data.cases[0].samples.append(existing_order_sample)

        user = sample_store.add_user(customer=old_customer, email=user_mail, name=user_name)

        # WHEN calling submit
        # THEN an OrderError should not be raised on illegal customer
        orders_api.submit(
            raw_order=order_data.model_dump(by_alias=True), user=user, order_type=order_type
        )


@pytest.mark.xfail(reason="Change in order validation")
@pytest.mark.parametrize(
    "order_type",
    [OrderType.MIP_DNA, OrderType.MIP_RNA, OrderType.BALSAMIC],
)
def test_submit_duplicate_sample_case_name(
    all_orders_to_submit: dict,
    monkeypatch: pytest.MonkeyPatch,
    order_type: OrderType,
    orders_api: OrdersAPI,
    ticket_id: str,
    user_mail: str,
    user_name: str,
):
    # GIVEN we have an order with a case that is already in the database
    order_data = OrderIn.parse_obj(obj=all_orders_to_submit[order_type], project=order_type)
    store = orders_api.status
    customer: Customer = store.get_customer_by_internal_id(customer_internal_id=order_data.customer)
    for sample in order_data.samples:
        case_id = sample.family_name
        if not store.get_case_by_name_and_customer(customer=customer, case_name=case_id):
            case: Case = store.add_case(
                data_analysis=Workflow.MIP_DNA,
                data_delivery=DataDelivery.SCOUT,
                name=case_id,
                ticket=ticket_id,
            )
            case.customer = customer
            store.session.add(case)
        store.session.commit()
        assert store.get_case_by_name_and_customer(customer=customer, case_name=case_id)

    monkeypatch_process_lims(monkeypatch, order_data)

    # WHEN calling submit
    # THEN an OrderError should be raised on duplicate case name
    with pytest.raises(OrderError):
        orders_api.submit(
            project=order_type,
            order_in=order_data,
            user_name=user_name,
            user_mail=user_mail,
        )


@pytest.mark.xfail(reason="Change in order validation")
@pytest.mark.parametrize(
    "order_type",
    [OrderType.FLUFFY],
)
def test_submit_fluffy_duplicate_sample_case_name(
    all_orders_to_submit: dict,
    monkeypatch: pytest.MonkeyPatch,
    order_type: OrderType,
    orders_api: OrdersAPI,
    user_mail: str,
    user_name: str,
    ticket_id: str,
):
    with patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.create_ticket"
    ) as mock_create_ticket, patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.reply_to_ticket"
    ) as mock_reply_to_ticket:
        mock_freshdesk_ticket_creation(mock_create_ticket, ticket_id)
        mock_freshdesk_reply_to_ticket(mock_reply_to_ticket)
        # GIVEN we have an order with a case that is already in the database
        order_data = OrderIn.parse_obj(obj=all_orders_to_submit[order_type], project=order_type)
        monkeypatch_process_lims(monkeypatch, order_data)

        orders_api.submit(
            project=order_type, order_in=order_data, user_name=user_name, user_mail=user_mail
        )

        # WHEN calling submit
        # THEN an OrderError should be raised on duplicate case name
        with pytest.raises(OrderError):
            orders_api.submit(
                project=order_type,
                order_in=order_data,
                user_name=user_name,
                user_mail=user_mail,
            )


@pytest.mark.xfail(reason="Change in order validation")
def test_submit_unique_sample_case_name(
    orders_api: OrdersAPI,
    mip_dna_order_to_submit: dict,
    user_name: str,
    user_mail: str,
    monkeypatch: pytest.MonkeyPatch,
    ticket_id: str,
):
    with patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.create_ticket"
    ) as mock_create_ticket, patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.reply_to_ticket"
    ) as mock_reply_to_ticket:
        mock_freshdesk_ticket_creation(mock_create_ticket, ticket_id)
        mock_freshdesk_reply_to_ticket(mock_reply_to_ticket)

        # GIVEN we have an order with a case that is not existing in the database
        order_data = OrderIn.parse_obj(obj=mip_dna_order_to_submit, project=OrderType.MIP_DNA)

        store = orders_api.status
        for sample in order_data.samples:
            case_id = sample.family_name
            customer: Customer = store.get_customer_by_internal_id(
                customer_internal_id=order_data.customer
            )
            assert not store.get_case_by_name_and_customer(customer=customer, case_name=case_id)

        monkeypatch_process_lims(monkeypatch, order_data)

        # WHEN calling submit
        orders_api.submit(
            project=OrderType.MIP_DNA,
            order_in=order_data,
            user_name=user_name,
            user_mail=user_mail,
        )

        # Then no exception about duplicate names should be thrown


@pytest.mark.xfail(reason="Change in order validation")
@pytest.mark.parametrize(
    "order_type",
    [
        OrderType.BALSAMIC,
        OrderType.FASTQ,
        OrderType.FLUFFY,
        OrderType.METAGENOME,
        OrderType.MICROSALT,
        OrderType.MIP_DNA,
        OrderType.MIP_RNA,
        OrderType.RML,
        OrderType.SARS_COV_2,
    ],
)
def test_submit_unique_sample_name(
    all_orders_to_submit: dict,
    monkeypatch: pytest.MonkeyPatch,
    order_type: OrderType,
    orders_api: OrdersAPI,
    user_mail: str,
    user_name: str,
    ticket_id: str,
):
    with patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.create_ticket"
    ) as mock_create_ticket, patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.reply_to_ticket"
    ) as mock_reply_to_ticket:
        mock_freshdesk_ticket_creation(mock_create_ticket, ticket_id)
        mock_freshdesk_reply_to_ticket(mock_reply_to_ticket)
        # GIVEN we have an order with a sample that is not existing in the database
        order_data = OrderIn.parse_obj(obj=all_orders_to_submit[order_type], project=order_type)
        store = orders_api.validation_service.store
        assert not store._get_query(table=Sample).first()

        monkeypatch_process_lims(monkeypatch, order_data)

        # WHEN calling submit
        orders_api.submit(
            project=order_type, order_in=order_data, user_name=user_name, user_mail=user_mail
        )

        # Then no exception about duplicate names should be thrown


@pytest.mark.xfail(reason="Change in order validation")
@pytest.mark.parametrize(
    "order_type",
    [OrderType.SARS_COV_2, OrderType.METAGENOME],
)
def test_sarscov2_submit_duplicate_sample_name(
    all_orders_to_submit: dict,
    helpers: StoreHelpers,
    monkeypatch: pytest.MonkeyPatch,
    order_type: OrderType,
    orders_api: OrdersAPI,
    user_mail: str,
    user_name: str,
):
    # GIVEN we have an order with samples that is already in the database
    order_data = OrderIn.parse_obj(obj=all_orders_to_submit[order_type], project=order_type)
    monkeypatch_process_lims(monkeypatch, order_data)
    store_samples_with_names_from_order(orders_api.status, helpers, order_data)

    # WHEN calling submit
    # THEN an OrderError should be raised on duplicate sample name
    with pytest.raises(OrderError):
        orders_api.submit(
            project=order_type,
            order_in=order_data,
            user_name=user_name,
            user_mail=user_mail,
        )


def store_samples_with_names_from_order(store: Store, helpers: StoreHelpers, order_data: OrderIn):
    customer: Customer = store.get_customer_by_internal_id(customer_internal_id=order_data.customer)
    for sample in order_data.samples:
        sample_name = sample.name
        if not store.get_sample_by_customer_and_name(
            customer_entry_id=[customer.id], sample_name=sample_name
        ):
            sample_obj = helpers.add_sample(
                store=store, customer_id=customer.internal_id, name=sample_name
            )
            store.session.add(sample_obj)
            store.session.commit()


@pytest.mark.xfail(reason="Change in order validation")
@pytest.mark.parametrize(
    "order_type",
    [
        OrderType.BALSAMIC,
        OrderType.FASTQ,
        OrderType.MICROSALT,
        OrderType.MIP_DNA,
        OrderType.MIP_RNA,
        OrderType.RML,
    ],
)
def test_not_sarscov2_submit_duplicate_sample_name(
    all_orders_to_submit: dict,
    helpers: StoreHelpers,
    monkeypatch: pytest.MonkeyPatch,
    order_type: OrderType,
    orders_api: OrdersAPI,
    user_mail: str,
    user_name: str,
    ticket_id: str,
):
    with patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.create_ticket"
    ) as mock_create_ticket, patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.reply_to_ticket"
    ) as mock_reply_to_ticket:
        mock_freshdesk_ticket_creation(mock_create_ticket, ticket_id)
        mock_freshdesk_reply_to_ticket(mock_reply_to_ticket)
        # GIVEN we have an order with samples that is already in the database
        order_data = OrderIn.parse_obj(obj=all_orders_to_submit[order_type], project=order_type)
        monkeypatch_process_lims(monkeypatch, order_data)
        store_samples_with_names_from_order(orders_api.status, helpers, order_data)

        # WHEN calling submit
        orders_api.submit(
            project=order_type, order_in=order_data, user_name=user_name, user_mail=user_mail
        )

        # THEN no OrderError should be raised on duplicate sample name
