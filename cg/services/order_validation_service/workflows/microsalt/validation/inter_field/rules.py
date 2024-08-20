from cg.constants.constants import PrepCategory, Workflow
from cg.services.order_validation_service.constants import WORKFLOW_PREP_CATEGORIES
from cg.services.order_validation_service.errors.sample_errors import ApplicationNotCompatibleError
from cg.services.order_validation_service.validators.inter_field.utils import (
    _is_application_not_compatible,
)
from cg.services.order_validation_service.workflows.microsalt.models.order import MicrosaltOrder
from cg.store.store import Store


def validate_application_compatibility(
    order: MicrosaltOrder,
    store: Store,
    **kwargs,
) -> list[ApplicationNotCompatibleError]:
    errors: list[ApplicationNotCompatibleError] = []
    workflow: Workflow = order.workflow
    allowed_prep_categories: list[PrepCategory] = WORKFLOW_PREP_CATEGORIES[workflow]
    for sample_index, sample in order.enumerated_new_samples:
        incompatible: bool = _is_application_not_compatible(
            allowed_prep_categories=allowed_prep_categories,
            application_tag=sample.application,
            store=store,
        )
        if incompatible:
            error = ApplicationNotCompatibleError(sample_index=sample_index)
            errors.append(error)
    return errors
