from cg.services.orders.validation.errors.case_errors import (
    DoubleNormalError,
    DoubleTumourError,
    MoreThanTwoSamplesInCaseError,
    NormalOnlyWGSError,
    NumberOfNormalSamplesError,
)
from cg.services.orders.validation.errors.case_sample_errors import (
    CaptureKitMissingError,
    InvalidCaptureKitError,
)
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.order_types.balsamic.models.case import BalsamicCase
from cg.services.orders.validation.order_types.balsamic.models.order import BalsamicOrder
from cg.services.orders.validation.order_types.balsamic.models.sample import BalsamicSample
from cg.services.orders.validation.rules.case.rules import (
    validate_at_most_two_samples_per_case,
    validate_number_of_normal_samples,
)
from cg.services.orders.validation.rules.case_sample.rules import (
    validate_capture_kit_requirement,
    validate_capture_kit,
)
from cg.store.models import Application
from cg.store.store import Store
from tests.services.orders.validation_service.workflows.balsamic.conftest import (
    create_case,
    create_order,
)
from tests.store_helpers import StoreHelpers


def test_validate_capture_kit_required(
    valid_order: BalsamicOrder, base_store: Store, application_tgs: Application
):

    # GIVEN an order with a TGS sample but missing capture kit
    valid_order.cases[0].samples[0].application = application_tgs.tag
    valid_order.cases[0].samples[0].capture_kit = None

    # WHEN validating that the order has required capture kits set
    errors: list[CaptureKitMissingError] = validate_capture_kit_requirement(
        order=valid_order, store=base_store
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the missing capture kit
    assert isinstance(errors[0], CaptureKitMissingError)


def test_validate_capture_kit(
    valid_order: BalsamicOrder, base_store: Store, application_tgs: Application
):

    # GIVEN an order with a capture kit set with an invalid value
    valid_order.cases[0].samples[0].application = application_tgs.tag
    valid_order.cases[0].samples[0].capture_kit = "invalid name"

    # WHEN validating that the order has a valid capture kit panel
    errors: list[InvalidCaptureKitError] = validate_capture_kit(order=valid_order, store=base_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the invalid capture kit
    assert isinstance(errors[0], InvalidCaptureKitError)


def test_more_than_two_samples_in_case(
    valid_order: BalsamicOrder,
    another_balsamic_sample: BalsamicSample,
    a_third_balsamic_sample: BalsamicSample,
):
    # GIVEN a Balsamic order with three samples in the same case

    valid_order.cases[0].samples.append(another_balsamic_sample)
    valid_order.cases[0].samples.append(a_third_balsamic_sample)

    # WHEN validating that the order has at most one sample per case
    errors: list[MoreThanTwoSamplesInCaseError] = validate_at_most_two_samples_per_case(valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the multiple samples in the first case
    assert isinstance(errors[0], MoreThanTwoSamplesInCaseError)
    assert errors[0].case_index == 0


def test_double_tumour_samples_in_case(
    valid_order: BalsamicOrder, another_balsamic_sample: BalsamicSample, base_store: Store
):
    # GIVEN a Balsamic order with two samples in a case
    valid_order.cases[0].samples.append(another_balsamic_sample)

    # GIVEN that both samples are tumours
    valid_order.cases[0].samples[0].tumour = True
    valid_order.cases[0].samples[1].tumour = True

    # WHEN validating that the order has at most one sample per case
    errors: list[NumberOfNormalSamplesError] = validate_number_of_normal_samples(
        order=valid_order, store=base_store
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the double tumours in the case
    assert isinstance(errors[0], DoubleTumourError)
    assert errors[0].case_index == 0


def test_double_normal_samples_in_case(
    valid_order: BalsamicOrder, another_balsamic_sample: BalsamicSample, base_store: Store
):
    # GIVEN a Balsamic order with two samples in a case
    valid_order.cases[0].samples.append(another_balsamic_sample)

    # GIVEN that both samples are tumours
    valid_order.cases[0].samples[0].tumour = False
    valid_order.cases[0].samples[1].tumour = False

    # WHEN validating that the order has at most one sample per case
    errors: list[NumberOfNormalSamplesError] = validate_number_of_normal_samples(
        order=valid_order, store=base_store
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the double tumours in the case
    assert isinstance(errors[0], DoubleNormalError)
    assert errors[0].case_index == 0


def test_normal_only_wgs_in_case_with_new_sample(
    valid_order: BalsamicOrder, base_store: Store, wgs_application_tag: str
):

    # GIVEN that the sample in the order is WGS and normal
    valid_order.cases[0].samples[0].application = wgs_application_tag
    valid_order.cases[0].samples[0].tumour = False

    # WHEN validating that the order contains only one sample that is normal and WGS
    errors: list[NumberOfNormalSamplesError] = validate_number_of_normal_samples(
        order=valid_order, store=base_store
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern that case having only one sample that is normal and WGS
    assert isinstance(errors[0], NormalOnlyWGSError)
    assert errors[0].case_index == 0
    assert len(valid_order.cases[0].samples) == 1


def test_normal_only_wgs_in_case_with_existing_sample(
    store_to_submit_and_validate_orders: Store, helpers: StoreHelpers, wgs_application_tag: str
):

    # GIVEN a store with a wgs normal sample
    helpers.add_sample(
        store=store_to_submit_and_validate_orders,
        application_tag=wgs_application_tag,
        internal_id="wgs_normal_sample",
        is_tumour=False,
    )

    # GIVEN an order with this existing sample
    sample = ExistingSample(
        internal_id="wgs_normal_sample",
    )
    case: BalsamicCase = create_case([sample])
    order: BalsamicOrder = create_order([case])

    # WHEN validating if the order contains only one sample that is normal and WGS
    errors: list[NumberOfNormalSamplesError] = validate_number_of_normal_samples(
        order=order, store=store_to_submit_and_validate_orders
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern that case having only one sample that is normal and WGS
    assert isinstance(errors[0], NormalOnlyWGSError)
    assert errors[0].case_index == 0
    assert len(order.cases[0].samples) == 1
