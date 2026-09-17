from unittest.mock import Mock, create_autospec

from cg.services.orders.validation.order_types.microsalt.models.order import MicrosaltOrder
from cg.services.orders.validation.order_types.raredisease.models.order import RarediseaseOrder
from cg.store.models import Application
from cg.store.store import Store


def test_external_samples_order_with_cases(raredisease_order: RarediseaseOrder):
    # GIVEN a StatusDB
    status_db: Store = create_autospec(Store)

    # GIVEN a raredisease order

    # GIVEN that the first sample is external
    status_db.get_application_by_tag_strict = Mock(
        side_effect=[
            create_autospec(Application, is_external=True),
            create_autospec(Application, is_external=False),
            create_autospec(Application, is_external=False),
            create_autospec(Application, is_external=False),
        ]
    )

    # WHEN getting the external samples of the order
    external_samples = raredisease_order.external_samples(status_db)

    # THEN only the first sample should be returned
    assert external_samples == [raredisease_order.enumerated_new_samples[0][2]]


def test_external_samples_order_with_samples(microsalt_order: MicrosaltOrder):
    # GIVEN a StatusDB
    status_db: Store = create_autospec(Store)

    # GIVEN a microsalt order

    # GIVEN that the first sample is external
    status_db.get_application_by_tag_strict = Mock(
        side_effect=[
            create_autospec(Application, is_external=True),
            create_autospec(Application, is_external=False),
            create_autospec(Application, is_external=False),
            create_autospec(Application, is_external=False),
            create_autospec(Application, is_external=False),
        ]
    )

    # WHEN getting the external samples of the order
    external_samples = microsalt_order.external_samples(status_db)

    # THEN only the first sample should be returned
    assert external_samples == [microsalt_order.samples[0]]
