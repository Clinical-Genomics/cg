import datetime as dt

import pytest

from cg.store import models
from cg.meta.orders.api import OrdersAPI, OrderType


@pytest.mark.parametrize('order_type', [
    OrderType.RML,
    OrderType.FASTQ,
    OrderType.SCOUT,
    OrderType.EXTERNAL,
])
def test_submit(base_store, orders_api, all_orders, monkeypatch, order_type):
    ticket_number = 1234567
    monkeypatch.setattr(orders_api.osticket, 'open_ticket', lambda *args, **kwargs: ticket_number)

    order_data = all_orders[order_type]
    lims_project_data = {'id': 'ADM1234', 'date': dt.datetime.now()}
    lims_map = {sample['name']: f"ELH123A{index}" for index, sample in
                enumerate(order_data['samples'])}
    monkeypatch.setattr(orders_api, 'process_lims', lambda *args: (lims_project_data, lims_map))

    # GIVEN an order and an empty store
    assert base_store.samples().first() is None
    # WHEN submitting the order
    result = orders_api.submit(order_type, 'Paul Anderson', 'paul@magnolia.com', order_data)
    # THEN it should work...
    for record in result['records']:
        if isinstance(record, models.Pool) or isinstance(record, models.Sample):
            assert record.ticket_number == ticket_number
        else:
            assert isinstance(record, models.Family)
            for link_obj in record.links:
                assert link_obj.sample.ticket_number == ticket_number
