import datetime as dt

import pytest
from cg.constants import DataDelivery

from cg.exc import OrderError
from cg.meta.orders import OrdersAPI
from cg.models.orders.order import OrderIn, OrderType
from cg.models.orders.samples import MipDnaSample
from cg.store import models
from cgmodels.cg.constants import Pipeline
import cg
from tests.store_helpers import StoreHelpers

PROCESS_LIMS_FUNCTION = "cg.meta.orders.api.process_lims"


def test_too_long_order_name():
    # GIVEN order with more than allowed characters name
    long_name = "A super long order name that is longer than sixty-four characters."
    assert len(long_name) > models.Sample.order.property.columns[0].type.length

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
        OrderType.SARS_COV_2,
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
    lims_map = {sample.name: f"ELH123A{index}" for index, sample in enumerate(order_data.samples)}
    monkeypatch.setattr(
        PROCESS_LIMS_FUNCTION,
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
    [OrderType.MIP_DNA, OrderType.MIP_RNA, OrderType.BALSAMIC],
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
    lims_map = {sample.name: f"ELH123A{index}" for index, sample in enumerate(order_data.samples)}
    monkeypatch.setattr(PROCESS_LIMS_FUNCTION, lambda **kwargs: (lims_project_data, lims_map))

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
        sample.internal_id = existing_sample.internal_id

    # WHEN calling submit
    # THEN an OrderError should be raised on illegal customer
    with pytest.raises(OrderError):
        orders_api.submit(
            project=order_type, order_in=order_data, user_name=user_name, user_mail=user_mail
        )


@pytest.mark.parametrize(
    "order_type",
    [OrderType.MIP_DNA, OrderType.MIP_RNA, OrderType.BALSAMIC],
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
    lims_map = {sample.name: f"ELH123A{index}" for index, sample in enumerate(order_data.samples)}
    monkeypatch.setattr(PROCESS_LIMS_FUNCTION, lambda **kwargs: (lims_project_data, lims_map))
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

    for sample in order_data.samples:
        sample.internal_id = existing_sample.internal_id
        break

    # WHEN calling submit
    # THEN an OrderError should not be raised on illegal customer
    orders_api.submit(
        project=order_type, order_in=order_data, user_name=user_name, user_mail=user_mail
    )


def test_submit_duplicate_sample_case_name(
    orders_api, mip_order_to_submit, ticket_number: int, user_name: str, user_mail: str, mocker
):
    # GIVEN we have an order with a case that is already in the database
    order_data = OrderIn.parse_obj(obj=mip_order_to_submit, project=OrderType.MIP_DNA)
    store = orders_api.status
    customer_obj = store.customer(order_data.customer)

    for sample in order_data.samples:
        case_id = sample.family_name
        if not store.find_family(customer=customer_obj, name=case_id):
            case_obj = store.add_case(
                data_analysis=Pipeline.MIP_DNA,
                data_delivery=DataDelivery.SCOUT,
                name=case_id,
                panels=None,
            )
            case_obj.customer = customer_obj
            store.add_commit(case_obj)
        assert store.find_family(customer=customer_obj, name=case_id)

    mocker.patch(PROCESS_LIMS_FUNCTION)

    # WHEN calling submit
    # THEN an OrderError should be raised on duplicate case name
    with pytest.raises(OrderError):
        orders_api.submit(
            project=OrderType.MIP_DNA, order_in=order_data, user_name=user_name, user_mail=user_mail
        )

    # Then no new samples should have been created in LIMS
    cg.meta.orders.api.process_lims.assert_not_called()


def test_submit_unique_sample_case_name(
    orders_api, mip_order_to_submit, ticket_number: int, user_name: str, user_mail: str, monkeypatch
):
    # GIVEN we have an order with a case that is not existing in the database
    order_data = OrderIn.parse_obj(obj=mip_order_to_submit, project=OrderType.MIP_DNA)

    store = orders_api.status

    sample: MipDnaSample
    for sample in order_data.samples:
        case_id = sample.family_name
        customer_obj = store.customer(order_data.customer)
        assert not store.find_family(customer=customer_obj, name=case_id)

    lims_project_data = {"id": "ADM1234", "date": dt.datetime.now()}
    lims_map = {sample.name: f"ELH123A{index}" for index, sample in enumerate(order_data.samples)}
    monkeypatch.setattr(PROCESS_LIMS_FUNCTION, lambda **kwargs: (lims_project_data, lims_map))

    # WHEN calling submit
    orders_api.submit(
        project=OrderType.MIP_DNA, order_in=order_data, user_name=user_name, user_mail=user_mail
    )

    # Then no exception about duplicate names should be thrown


def test_validate_sex_inconsistent_sex(
    orders_api: OrdersAPI, mip_order_to_submit: dict, helpers: StoreHelpers
):
    # GIVEN we have an order with a sample that is already in the database but with different sex
    order_data = OrderIn.parse_obj(mip_order_to_submit, project=OrderType.MIP_DNA)
    store = orders_api.status
    customer_obj = store.customer(order_data.customer)

    # add sample with different sex than in order
    sample: MipDnaSample
    for sample in order_data.samples:
        sample_obj: models.Sample = helpers.add_sample(
            store=store,
            subject_id=sample.subject_id,
            name=sample.name,
            gender="male" if sample.sex == "female" else "female",
            customer_id=customer_obj.internal_id,
        )
        store.add_commit(sample_obj)
        assert sample_obj.sex != sample.sex

    # WHEN calling _validate_sex
    # THEN an OrderError should be raised on non-matching sex
    with pytest.raises(OrderError):
        orders_api._validate_subject_sex(
            samples=order_data.samples, customer_id=order_data.customer
        )


def test_validate_sex_consistent_sex(
    orders_api: OrdersAPI, mip_order_to_submit: dict, helpers: StoreHelpers
):
    # GIVEN we have an order with a sample that is already in the database and with same gender
    order_data = OrderIn.parse_obj(mip_order_to_submit, project=OrderType.MIP_DNA)
    store = orders_api.status
    customer_obj = store.customer(order_data.customer)

    # add sample with different sex than in order
    sample: MipDnaSample
    for sample in order_data.samples:
        sample_obj: models.Sample = helpers.add_sample(
            store=store,
            subject_id=sample.subject_id,
            name=sample.name,
            gender=sample.sex,
            customer_id=customer_obj.internal_id,
        )
        store.add_commit(sample_obj)
        assert sample_obj.sex == sample.sex

    # WHEN calling _validate_sex
    orders_api._validate_subject_sex(samples=order_data.samples, customer_id=order_data.customer)

    # THEN no OrderError should be raised on non-matching sex


def test_validate_sex_unknown_existing_sex(
    orders_api: OrdersAPI, mip_order_to_submit: dict, helpers: StoreHelpers
):
    # GIVEN we have an order with a sample that is already in the database and with different gender but the existing is
    # of type "unknown"
    order_data = OrderIn.parse_obj(mip_order_to_submit, project=OrderType.MIP_DNA)
    store = orders_api.status
    customer_obj = store.customer(order_data.customer)

    # add sample with different sex than in order
    sample: MipDnaSample
    for sample in order_data.samples:
        sample_obj: models.Sample = helpers.add_sample(
            store=store,
            subject_id=sample.subject_id,
            name=sample.name,
            gender="unknown",
            customer_id=customer_obj.internal_id,
        )
        store.add_commit(sample_obj)
        assert sample_obj.sex != sample.sex

    # WHEN calling _validate_sex
    orders_api._validate_subject_sex(samples=order_data.samples, customer_id=order_data.customer)

    # THEN no OrderError should be raised on non-matching sex


def test_validate_sex_unknown_new_sex(
    orders_api: OrdersAPI, mip_order_to_submit: dict, helpers: StoreHelpers
):
    # GIVEN we have an order with a sample that is already in the database and with different gender but the new is of
    # type "unknown"
    order_data = OrderIn.parse_obj(mip_order_to_submit, project=OrderType.MIP_DNA)
    store = orders_api.status
    customer_obj = store.customer(order_data.customer)

    # add sample with different sex than in order
    for sample in order_data.samples:
        sample_obj: models.Sample = helpers.add_sample(
            store=store,
            subject_id=sample.subject_id,
            name=sample.name,
            gender=sample.sex,
            customer_id=customer_obj.internal_id,
        )
        sample.sex = "unknown"
        store.add_commit(sample_obj)

    for sample in order_data.samples:
        assert sample_obj.sex != sample.sex

    # WHEN calling _validate_sex
    orders_api._validate_subject_sex(samples=order_data.samples, customer_id=order_data.customer)

    # THEN no OrderError should be raised on non-matching sex
