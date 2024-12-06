from cg.services.order_validation_service.errors.case_sample_errors import CaptureKitMissingError
from cg.services.order_validation_service.workflows.balsamic.models.order import BalsamicOrder
from cg.services.order_validation_service.workflows.balsamic.rules.case_sample.utils import (
    is_sample_missing_capture_kit,
)
from cg.store.store import Store


def validate_capture_kit_panel_requirement(
    order: BalsamicOrder, store: Store
) -> list[CaptureKitMissingError]:
    errors: list[CaptureKitMissingError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if is_sample_missing_capture_kit(sample=sample, store=store):
                error = CaptureKitMissingError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors
