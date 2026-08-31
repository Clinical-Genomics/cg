from unittest.mock import create_autospec

from cg.services.orders.validation.order_types.raredisease.models.order import RarediseaseOrder
from cg.store.store import Store


def test_external_samples_order_with_cases(raredisease_order: RarediseaseOrder):
    # GIVEN a StatusDB
    status_db: Store = create_autospec(Store)

    # GIVEN a raredisease order

    # GIVEN that the first sample is external

    # WHEN getting the external samples of the order

    # THEN only the first sample should be returned
