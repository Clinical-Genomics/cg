from cg.services.order_validation_service.errors.sample_errors import (
    SampleNameNotAvailableError,
)
from cg.services.order_validation_service.rules.sample.rules import (
    validate_sample_names_available,
)
from cg.services.order_validation_service.workflows.microsalt.models.order import (
    MicrosaltOrder,
)
from cg.store.models import Sample
from cg.store.store import Store


def test_sample_names_available(valid_order: MicrosaltOrder, sample_store: Store):

    # GIVEN an order with a sample name reused from a previous order
    sample = sample_store.session.query(Sample).first()
    valid_order.customer = sample.customer.internal_id
    valid_order.samples[0].name = sample.name

    # WHEN validating that the sample names are available to the customer
    errors = validate_sample_names_available(order=valid_order, store=sample_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the reused sample name
    assert isinstance(errors[0], SampleNameNotAvailableError)
