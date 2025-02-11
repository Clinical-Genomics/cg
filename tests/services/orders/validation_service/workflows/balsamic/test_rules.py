from cg.services.orders.validation.errors.case_errors import (
    DoubleNormalError,
    DoubleTumourError,
    MoreThanTwoSamplesInCaseError,
    NumberOfNormalSamplesError,
    NormalOnlyWGSError,
)
from cg.services.orders.validation.errors.case_sample_errors import CaptureKitMissingError
from cg.services.orders.validation.rules.case.rules import (
    validate_at_most_two_samples_per_case,
    validate_number_of_normal_samples,
)
from cg.services.orders.validation.rules.case_sample.rules import (
    validate_capture_kit_panel_requirement,
)
from cg.services.orders.validation.workflows.balsamic.models.order import BalsamicOrder
from cg.services.orders.validation.workflows.balsamic.models.sample import BalsamicSample
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


def test_normal_only_wgs_in_case_with_new_sample(valid_order: BalsamicOrder, base_store: Store):

    # GIVEN that the sample in the order is WGS and normal
    valid_order.cases[0].samples[0].application = "WGSPCFC030"
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


def test_normal_only_wgs_in_case_with_existing_sample(
    valid_order_with_existing_sample: BalsamicOrder, store_with_existing_sample: Store
):

    # GIVEN an order with an existing sample and a store with the corresponding sample
    # GIVEN that the sample is normal and WGS

    # WHEN validating if the order contains only one sample that is normal and WGS
    errors: list[NumberOfNormalSamplesError] = validate_number_of_normal_samples(
        order=valid_order_with_existing_sample, store=store_with_existing_sample
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern that case having only one sample that is normal and WGS
    assert isinstance(errors[0], NormalOnlyWGSError)
    assert errors[0].case_index == 0
