from cg.services.order_validation_service.errors.case_sample_errors import CaptureKitMissingError
from cg.services.order_validation_service.workflows.balsamic.models.order import BalsamicOrder
from cg.services.order_validation_service.workflows.balsamic.rules.case_sample.rules import (
    validate_capture_kit_panel_requirement,
)
from cg.store.models import Application
from cg.store.store import Store


def test_validate_capture_kit_required(
    valid_order: BalsamicOrder, base_store: Store, application_tgs: Application
):

    # GIVEN an order with a TGS sample but missing capture kit
    valid_order.cases[0].samples[0].application = application_tgs.tag
    valid_order.cases[0].samples[0].capture_kit = None

    # WHEN validating that the order has required capture kits set
    errors: list[CaptureKitMissingError] = validate_capture_kit_panel_requirement(
        order=valid_order, store=base_store
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the missing capture kit
    assert isinstance(errors[0], CaptureKitMissingError)
