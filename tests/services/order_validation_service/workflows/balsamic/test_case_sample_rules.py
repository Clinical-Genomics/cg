from cg.models.orders.sample_base import SexEnum
from cg.services.order_validation_service.errors.case_sample_errors import (
    CaptureKitMissingError,
    SexSubjectIdError,
)
from cg.services.order_validation_service.workflows.balsamic.models.order import (
    BalsamicOrder,
)
from cg.services.order_validation_service.workflows.balsamic.rules.case_sample.rules import (
    validate_capture_kit_panel_requirement,
    validate_subject_sex_consistency,
)
from cg.store.models import Application, Sample
from cg.store.store import Store


def test_validate_sex_subject_id_clash(valid_order: BalsamicOrder, sample_store: Store):
    # GIVEN an existing sample
    sample = sample_store.session.query(Sample).first()

    # GIVEN an order and sample with the same customer and subject id
    valid_order.customer = sample.customer.internal_id
    valid_order.cases[0].samples[0].subject_id = "subject"
    sample.subject_id = "subject"

    # GIVEN a sample in the order that has a different sex
    valid_order.cases[0].samples[0].sex = SexEnum.female
    sample.sex = SexEnum.male

    # WHEN validating the order
    errors = validate_subject_sex_consistency(
        order=valid_order,
        store=sample_store,
    )

    # THEN an error should be given for the clash
    assert errors
    assert isinstance(errors[0], SexSubjectIdError)


def test_validate_capture_kit_required(
    valid_order: BalsamicOrder, base_store: Store, application_tgs: Application
):

    # GIVEN an order with a TGS sample but missing capture kit
    valid_order.cases[0].samples[0].application = application_tgs.tag
    valid_order.cases[0].samples[0].capture_kit = None

    # WHEN validating that the order has required capture kits set
    errors = validate_capture_kit_panel_requirement(order=valid_order, store=base_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the missing capture kit
    assert isinstance(errors[0], CaptureKitMissingError)
