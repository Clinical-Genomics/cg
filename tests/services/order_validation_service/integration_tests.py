from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.validation_service import (
    TomteValidationService,
)
from cg.store.store import Store


def test_valid_order(valid_order: TomteOrder, base_store: Store):
    tomte_validation_service = TomteValidationService(store=base_store)
    errors = tomte_validation_service.validate(valid_order.model_dump_json())
    assert not errors
