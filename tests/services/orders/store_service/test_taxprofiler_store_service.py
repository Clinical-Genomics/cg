"""
Module to test the store_order_data_in_status_db method of the StoreTaxprofilerOrderService class.
The function store_order_data_in_status_db is never expected to fail, as its input order should
have always been validated before calling the function.
"""

from cg.services.orders.storing.implementations.taxprofiler_order_service import (
    StoreTaxprofilerOrderService,
)
from cg.services.orders.validation.order_types.taxprofiler.models.order import TaxprofilerOrder
from cg.store.models import Sample
from cg.store.store import Store


def test_store_taxprofiler_order_data_in_status_db(
    taxprofiler_order: TaxprofilerOrder,
    store_taxprofiler_order_service: StoreTaxprofilerOrderService,
    store_to_submit_and_validate_orders: Store,
    ticket_id_as_int: int,
):
    # GIVEN an order
    order: TaxprofilerOrder = taxprofiler_order

    # GIVEN a store with no samples nor cases
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert not store_to_submit_and_validate_orders.get_cases()

    # WHEN storing the order
    new_samples: list[Sample] = store_taxprofiler_order_service.store_order_data_in_status_db(order)

    # THEN the samples should have been stored
    db_samples: list[Sample] = store_to_submit_and_validate_orders._get_query(table=Sample).all()
    assert set(new_samples) == set(db_samples)

    # THEN the samples should have the correct application tag
    for sample in db_samples:
        assert sample.application_version.application.tag in ["METWPFR030"]

    # THEN the order should be stored
    assert store_to_submit_and_validate_orders.get_order_by_ticket_id(ticket_id_as_int)
