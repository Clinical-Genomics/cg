import datetime as dt

import pytest
from cg.exc import OrderError
from cg.meta.orders import OrdersAPI, OrderType
from cg.store import models


@pytest.mark.parametrize(
    "order_type",
    [
        OrderType.RML,
        OrderType.FASTQ,
        OrderType.MIP_DNA,
        OrderType.MIP_RNA,
        OrderType.EXTERNAL,
        OrderType.MICROSALT,
        OrderType.METAGENOME,
        OrderType.BALSAMIC,
    ],
)
def test_submit(
    base_store,
    orders_api: OrdersAPI,
    all_orders_to_submit,
    monkeypatch,
    order_type,
    user_name: str,
    user_mail: str,
    ticket_number: int,
):
    order_data = all_orders_to_submit[order_type]
    lims_project_data = {"id": "ADM1234", "date": dt.datetime.now()}
    lims_map = {
        sample["name"]: f"ELH123A{index}" for index, sample in enumerate(order_data.samples)
    }
    monkeypatch.setattr(
        "cg.meta.orders.api.process_lims",
        lambda **kwargs: (lims_project_data, lims_map),
    )

    # GIVEN an order and an empty store
    assert base_store.samples().first() is None

    # WHEN submitting the order

    result = orders_api.submit(
        project=order_type, order_in=order_data, user_name=user_name, user_mail=user_mail
    )

    # THEN the result should contain the ticket number for the order
    for record in result["records"]:
        if isinstance(record, (models.Pool, models.Sample)):
            assert record.ticket_number == ticket_number
        elif isinstance(record, models.Family):
            for link_obj in record.links:
                assert link_obj.sample.ticket_number == ticket_number


@pytest.mark.parametrize(
    "order_type",
    [OrderType.MIP_DNA, OrderType.MIP_RNA, OrderType.EXTERNAL, OrderType.BALSAMIC],
)
def test_submit_illegal_sample_customer(
    sample_store,
    orders_api,
    all_orders_to_submit,
    monkeypatch,
    order_type,
    ticket_number: int,
    user_name: str,
    user_mail: str,
):

    order_data = all_orders_to_submit[order_type]
    lims_project_data = {"id": "ADM1234", "date": dt.datetime.now()}
    lims_map = {
        sample["name"]: f"ELH123A{index}" for index, sample in enumerate(order_data.samples)
    }
    monkeypatch.setattr(
        "cg.meta.orders.api.process_lims", lambda **kwargs: (lims_project_data, lims_map)
    )

    # GIVEN we have an order with a customer that is not in the same customer group as customer
    # that the samples originate from
    customer_group = sample_store.add_customer_group("customer999only", "customer 999 only group")
    sample_store.add_commit(customer_group)
    new_customer = sample_store.add_customer(
        "customer999",
        "customer 999",
        scout_access=True,
        invoice_address="dummy street",
        customer_group=customer_group,
        invoice_reference="dummy nr",
    )
    sample_store.add_commit(new_customer)
    existing_sample = sample_store.samples().first()
    existing_sample.customer = new_customer
    sample_store.add_commit(existing_sample)

    for sample in order_data.samples:
        sample["internal_id"] = existing_sample.internal_id

    # WHEN calling submit
    # THEN an OrderError should be raised on illegal customer
    with pytest.raises(OrderError):
        orders_api.submit(
            project=order_type, order_in=order_data, user_name=user_name, user_mail=user_mail
        )


@pytest.mark.parametrize(
    "order_type",
    [OrderType.MIP_DNA, OrderType.MIP_RNA, OrderType.EXTERNAL, OrderType.BALSAMIC],
)
def test_submit_scout_legal_sample_customer(
    sample_store,
    orders_api,
    all_orders_to_submit,
    monkeypatch,
    order_type,
    user_name: str,
    user_mail: str,
    ticket_number: int,
):

    order_data = all_orders_to_submit[order_type]
    lims_project_data = {"id": "ADM1234", "date": dt.datetime.now()}
    lims_map = {
        sample["name"]: f"ELH123A{index}" for index, sample in enumerate(order_data.samples)
    }
    monkeypatch.setattr(
        "cg.meta.orders.api.process_lims", lambda **kwargs: (lims_project_data, lims_map)
    )
    # GIVEN we have an order with a customer that is in the same customer group as customer
    # that the samples originate from
    customer_group = sample_store.add_customer_group("customer999only", "customer 999 only group")
    sample_store.add_commit(customer_group)
    sample_customer = sample_store.add_customer(
        "customer1",
        "customer 1",
        scout_access=True,
        invoice_address="dummy street 1",
        customer_group=customer_group,
        invoice_reference="dummy nr",
    )
    order_customer = sample_store.add_customer(
        "customer2",
        "customer 2",
        scout_access=True,
        invoice_address="dummy street 2",
        customer_group=customer_group,
        invoice_reference="dummy nr",
    )
    sample_store.add_commit(sample_customer)
    sample_store.add_commit(order_customer)
    existing_sample = sample_store.samples().first()
    existing_sample.customer = sample_customer
    sample_store.commit()
    order_data.customer = order_customer.internal_id
    first = True

    for sample in order_data.samples:
        if first:
            sample["internal_id"] = existing_sample.internal_id
            first = False

    # WHEN calling submit
    # THEN an OrderError should not be raised on illegal customer
    orders_api.submit(
        project=order_type, order_in=order_data, user_name=user_name, user_mail=user_mail
    )


@pytest.mark.parametrize(
    "order_type",
    [OrderType.RML, OrderType.FASTQ, OrderType.MICROSALT, OrderType.METAGENOME],
)
def test_submit_non_scout_legal_sample_customer(
    sample_store,
    orders_api,
    all_orders_to_submit,
    monkeypatch,
    order_type,
    user_name: str,
    user_mail: str,
    ticket_number: int,
):

    order_data = all_orders_to_submit[order_type]
    lims_project_data = {"id": "ADM1234", "date": dt.datetime.now()}
    lims_map = {
        sample["name"]: f"ELH123A{index}" for index, sample in enumerate(order_data.samples)
    }
    monkeypatch.setattr(
        "cg.meta.orders.api.process_lims", lambda **kwargs: (lims_project_data, lims_map)
    )

    # GIVEN we have an order with a customer that is in the same customer group as customer
    # that the samples originate from but on order types where this is dis-allowed
    customer_group = sample_store.add_customer_group("customer999only", "customer 999 only group")
    sample_store.add_commit(customer_group)
    sample_customer = sample_store.add_customer(
        "customer1",
        "customer 1",
        scout_access=True,
        invoice_address="dummy street 1",
        customer_group=customer_group,
        invoice_reference="dummy nr",
    )
    order_customer = sample_store.add_customer(
        "customer2",
        "customer 2",
        scout_access=True,
        invoice_address="dummy street 2",
        customer_group=customer_group,
        invoice_reference="dummy nr",
    )
    sample_store.add_commit(sample_customer)
    sample_store.add_commit(order_customer)
    existing_sample = sample_store.samples().first()
    existing_sample.customer = sample_customer
    sample_store.commit()
    order_data.customer = order_customer.internal_id
    first = True

    for sample in order_data.samples:
        if first:
            sample["internal_id"] = existing_sample.internal_id
            first = False

    # WHEN calling submit
    # THEN an OrderError should be raised on illegal customer
    with pytest.raises(OrderError):
        orders_api.submit(
            project=order_type, order_in=order_data, user_name=user_name, user_mail=user_mail
        )
