import datetime as dt
from unittest.mock import Mock, patch

import pytest

from cg.clients.freshdesk.models import TicketResponse
from cg.constants import DataDelivery
from cg.constants.constants import Workflow
from cg.constants.subject import Sex
from cg.exc import OrderError, TicketCreationError
from cg.meta.orders import OrdersAPI
from cg.models.orders.order import OrderIn, OrderType
from cg.models.orders.samples import MipDnaSample
from cg.services.orders.validate_order_services.validate_case_order import (
    ValidateCaseOrderService,
)
from cg.store.models import Case, Customer, Pool, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def monkeypatch_process_lims(monkeypatch, order_data) -> None:
    lims_project_data = {"id": "ADM1234", "date": dt.datetime.now()}
    lims_map = {sample.name: f"ELH123A{index}" for index, sample in enumerate(order_data.samples)}
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
        OrderType.MICROSALT,
        OrderType.MIP_DNA,
        OrderType.MIP_RNA,
        OrderType.RML,
        OrderType.RNAFUSION,
        OrderType.SARS_COV_2,
    ],
)
def test_submit(
    all_orders_to_submit: dict,
    base_store: Store,
    monkeypatch: pytest.MonkeyPatch,
    order_type: OrderType,
    orders_api: OrdersAPI,
    ticket_id: str,
    user_mail: str,
    user_name: str,
):
    with patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.create_ticket"
    ) as mock_create_ticket, patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.reply_to_ticket"
    ) as mock_reply_to_ticket:
        mock_freshdesk_ticket_creation(mock_create_ticket, ticket_id)
        mock_freshdesk_reply_to_ticket(mock_reply_to_ticket)

        order_data = OrderIn.parse_obj(obj=all_orders_to_submit[order_type], project=order_type)
        monkeypatch_process_lims(monkeypatch, order_data)

        # GIVEN an order and an empty store
        assert not base_store._get_query(table=Sample).first()

        # WHEN submitting the order

        result = orders_api.submit(
            project=order_type, order_in=order_data, user_name=user_name, user_mail=user_mail
        )

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
    "order_type",
    [OrderType.MIP_DNA, OrderType.MIP_RNA, OrderType.BALSAMIC],
)
def test_submit_ticketexception(
    all_orders_to_submit,
    orders_api: OrdersAPI,
    order_type: OrderType,
    user_mail: str,
    user_name: str,
):
    # GIVEN a mock Freshdesk ticket creation that raises TicketCreationError
    with patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.create_ticket",
        side_effect=TicketCreationError("ERROR"),
    ):
        # GIVEN an order that does not have a name (ticket_nr)
        order_data = OrderIn.parse_obj(obj=all_orders_to_submit[order_type], project=order_type)
        order_data.name = "dummy_name"

        # WHEN the order is submitted and a TicketCreationError raised
        # THEN the TicketCreationError is not excepted
        with pytest.raises(TicketCreationError):
            orders_api.submit(
                project=order_type,
                order_in=order_data,
                user_name=user_name,
                user_mail=user_mail,
            )


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
):
    order_data = OrderIn.parse_obj(obj=all_orders_to_submit[order_type], project=order_type)
    monkeypatch_process_lims(monkeypatch, order_data)
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
    existing_sample: Sample = sample_store._get_query(table=Sample).first()
    existing_sample.customer = new_customer
    sample_store.session.add(existing_sample)
    sample_store.session.commit()
    for sample in order_data.samples:
        sample.internal_id = existing_sample.internal_id

    # WHEN calling submit
    # THEN an OrderError should be raised on illegal customer
    with pytest.raises(OrderError):
        orders_api.submit(
            project=order_type,
            order_in=order_data,
            user_name=user_name,
            user_mail=user_mail,
        )


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
):
    with patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.create_ticket"
    ) as mock_create_ticket, patch(
        "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.reply_to_ticket"
    ) as mock_reply_to_ticket:
        mock_freshdesk_ticket_creation(mock_create_ticket, ticket_id)
        mock_freshdesk_reply_to_ticket(mock_reply_to_ticket)
        order_data = OrderIn.parse_obj(obj=all_orders_to_submit[order_type], project=order_type)
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
        existing_sample: Sample = sample_store._get_query(table=Sample).first()
        existing_sample.customer = sample_customer
        sample_store.session.commit()
        order_data.customer = order_customer.internal_id

        for sample in order_data.samples:
            sample.internal_id = existing_sample.internal_id
            break

        # WHEN calling submit
        # THEN an OrderError should not be raised on illegal customer
        orders_api.submit(
            project=order_type, order_in=order_data, user_name=user_name, user_mail=user_mail
        )


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


def test_submit_unique_sample_case_name(
    orders_api: OrdersAPI,
    mip_order_to_submit: dict,
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
        order_data = OrderIn.parse_obj(obj=mip_order_to_submit, project=OrderType.MIP_DNA)

        store = orders_api.status

        sample: MipDnaSample
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


def test_validate_sex_inconsistent_sex(
    orders_api: OrdersAPI, mip_order_to_submit: dict, helpers: StoreHelpers
):
    # GIVEN we have an order with a sample that is already in the database but with different sex
    order_data = OrderIn.parse_obj(mip_order_to_submit, project=OrderType.MIP_DNA)
    store = orders_api.status
    customer: Customer = store.get_customer_by_internal_id(customer_internal_id=order_data.customer)

    # add sample with different sex than in order
    sample: MipDnaSample
    for sample in order_data.samples:
        sample_obj: Sample = helpers.add_sample(
            store=store,
            customer_id=customer.internal_id,
            sex=Sex.MALE if sample.sex == Sex.FEMALE else Sex.FEMALE,
            name=sample.name,
            subject_id=sample.subject_id,
        )
        store.session.add(sample_obj)
        store.session.commit()
        assert sample_obj.sex != sample.sex

    validator = ValidateCaseOrderService(status_db=orders_api.status)

    # WHEN calling _validate_sex
    # THEN an OrderError should be raised on non-matching sex
    with pytest.raises(OrderError):
        validator._validate_subject_sex(samples=order_data.samples, customer_id=order_data.customer)


def test_validate_sex_consistent_sex(
    orders_api: OrdersAPI, mip_order_to_submit: dict, helpers: StoreHelpers
):
    # GIVEN we have an order with a sample that is already in the database and with same gender
    order_data = OrderIn.parse_obj(mip_order_to_submit, project=OrderType.MIP_DNA)
    store = orders_api.status
    customer: Customer = store.get_customer_by_internal_id(customer_internal_id=order_data.customer)

    # add sample with different sex than in order
    sample: MipDnaSample
    for sample in order_data.samples:
        sample_obj: Sample = helpers.add_sample(
            store=store,
            customer_id=customer.internal_id,
            sex=sample.sex,
            name=sample.name,
            subject_id=sample.subject_id,
        )
        store.session.add(sample_obj)
        store.session.commit()
        assert sample_obj.sex == sample.sex

    validator = ValidateCaseOrderService(status_db=orders_api.status)

    # WHEN calling _validate_sex
    validator._validate_subject_sex(samples=order_data.samples, customer_id=order_data.customer)

    # THEN no OrderError should be raised on non-matching sex


def test_validate_sex_unknown_existing_sex(
    orders_api: OrdersAPI, mip_order_to_submit: dict, helpers: StoreHelpers
):
    # GIVEN we have an order with a sample that is already in the database and with different gender but the existing is
    # of type "unknown"
    order_data = OrderIn.parse_obj(mip_order_to_submit, project=OrderType.MIP_DNA)
    store = orders_api.status
    customer: Customer = store.get_customer_by_internal_id(customer_internal_id=order_data.customer)

    # add sample with different sex than in order
    sample: MipDnaSample
    for sample in order_data.samples:
        sample_obj: Sample = helpers.add_sample(
            store=store,
            customer_id=customer.internal_id,
            sex=Sex.UNKNOWN,
            name=sample.name,
            subject_id=sample.subject_id,
        )
        store.session.add(sample_obj)
        store.session.commit()
        assert sample_obj.sex != sample.sex

    validator = ValidateCaseOrderService(status_db=orders_api.status)

    # WHEN calling _validate_sex
    validator._validate_subject_sex(samples=order_data.samples, customer_id=order_data.customer)

    # THEN no OrderError should be raised on non-matching sex


def test_validate_sex_unknown_new_sex(
    orders_api: OrdersAPI, mip_order_to_submit: dict, helpers: StoreHelpers
):
    # GIVEN we have an order with a sample that is already in the database and with different gender but the new is of
    # type "unknown"
    order_data = OrderIn.parse_obj(mip_order_to_submit, project=OrderType.MIP_DNA)
    store = orders_api.status
    customer: Customer = store.get_customer_by_internal_id(customer_internal_id=order_data.customer)

    # add sample with different sex than in order
    for sample in order_data.samples:
        sample_obj: Sample = helpers.add_sample(
            store=store,
            customer_id=customer.internal_id,
            sex=sample.sex,
            name=sample.name,
            subject_id=sample.subject_id,
        )
        sample.sex = "unknown"
        store.session.add(sample_obj)
        store.session.commit()

    for sample in order_data.samples:
        assert sample_obj.sex != sample.sex

    validator = ValidateCaseOrderService(status_db=orders_api.status)

    # WHEN calling _validate_sex
    validator._validate_subject_sex(samples=order_data.samples, customer_id=order_data.customer)

    # THEN no OrderError should be raised on non-matching sex


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
        store = orders_api.status
        assert not store._get_query(table=Sample).first()

        monkeypatch_process_lims(monkeypatch, order_data)

        # WHEN calling submit
        orders_api.submit(
            project=order_type, order_in=order_data, user_name=user_name, user_mail=user_mail
        )

        # Then no exception about duplicate names should be thrown


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
