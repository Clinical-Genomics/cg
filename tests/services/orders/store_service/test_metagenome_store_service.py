"""
Module to test the store_order_data_in_status_db method of the StoreMetagenomeOrderService class.
The function store_order_data_in_status_db is never expected to fail, as its input order should
have always been validated before calling the function.
"""

import pytest

from cg.services.orders.storing.implementations.metagenome_order_service import (
    StoreMetagenomeOrderService,
)
from cg.services.orders.validation.order_types.metagenome.models.order import MetagenomeOrder
from cg.services.orders.validation.order_types.taxprofiler.models.order import TaxprofilerOrder
from cg.store.models import Sample
from cg.store.store import Store


@pytest.mark.parametrize(
    "order_fixture",
    ["metagenome_order", "taxprofiler_order"],
    ids=["Metagenome", "Taxprofiler"],
)
def test_store_metagenome_order_data_in_status_db(
    order_fixture: str,
    store_metagenome_order_service: StoreMetagenomeOrderService,
    store_to_submit_and_validate_orders: Store,
    ticket_id_as_int: int,
    request: pytest.FixtureRequest,
):
    # GIVEN an order
    order: MetagenomeOrder | TaxprofilerOrder = request.getfixturevalue(order_fixture)

    # GIVEN a store with no samples nor cases
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert not store_to_submit_and_validate_orders.get_cases()

    # WHEN storing the order
    new_samples: list[Sample] = store_metagenome_order_service.store_order_data_in_status_db(order)

    # THEN the samples should have been stored
    db_samples: list[Sample] = store_to_submit_and_validate_orders._get_query(table=Sample).all()
    assert set(new_samples) == set(db_samples)

    # THEN the samples should have the correct application tag
    for sample in db_samples:
        assert sample.application_version.application.tag in ["METWPFR030", "METPCFR030"]

    # THEN the order should be stored
    assert store_to_submit_and_validate_orders.get_order_by_ticket_id(ticket_id_as_int)
