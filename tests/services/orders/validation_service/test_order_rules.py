from cg.services.orders.validation.errors.order_errors import (
    CustomerCannotSkipReceptionControlError,
    CustomerDoesNotExistError,
    UserNotAssociatedWithCustomerError,
)
from cg.services.orders.validation.order_types.tomte.models.order import TomteOrder
from cg.services.orders.validation.rules.order.rules import (
    validate_customer_can_skip_reception_control,
    validate_customer_exists,
    validate_user_belongs_to_customer,
)
from cg.store.models import Customer
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_validate_customer_can_skip_reception_control(base_store: Store, valid_order: TomteOrder):
    # GIVEN an order attempting to skip reception control from a not trusted customer
    customer: Customer = base_store.get_customer_by_internal_id(valid_order.customer)
    customer.is_trusted = False
    valid_order.skip_reception_control = True

    # WHEN validating that the customer can skip reception control
    errors: list[CustomerCannotSkipReceptionControlError] = (
        validate_customer_can_skip_reception_control(order=valid_order, store=base_store)
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the customer not being allowed to skip reception control
    assert isinstance(errors[0], CustomerCannotSkipReceptionControlError)


def test_validate_customer_does_not_exist(base_store: Store, valid_order: TomteOrder):
    # GIVEN an order from an unknown customer
    valid_order.customer = "Unknown customer"

    # WHEN validating that the customer exists
    errors: list[CustomerDoesNotExistError] = validate_customer_exists(
        order=valid_order, store=base_store
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the unknown customer
    assert isinstance(errors[0], CustomerDoesNotExistError)


def test_validate_user_belongs_to_customer(
    base_store: Store, valid_order: TomteOrder, helpers: StoreHelpers
):
    # GIVEN an order for a customer which the logged-in user does not have access to
    customer: Customer = base_store.get_customer_by_internal_id(valid_order.customer)
    helpers.ensure_user(store=base_store, customer=customer)
    customer.users = []

    # WHEN validating that the user belongs to the customer account
    errors: list[UserNotAssociatedWithCustomerError] = validate_user_belongs_to_customer(
        order=valid_order, store=base_store
    )

    # THEN an error should be raised
    assert errors

    # THEN the error should concern the user not belonging to the customer
    assert isinstance(errors[0], UserNotAssociatedWithCustomerError)


def test_validate_admin_bypass(base_store: Store, valid_order: TomteOrder, helpers: StoreHelpers):
    # GIVEN an order for a customer which the logged-in _admin_ user does not have access to
    customer: Customer = base_store.get_customer_by_internal_id(valid_order.customer)
    helpers.ensure_user(store=base_store, customer=customer, is_admin=True)
    customer.users = []

    # WHEN validating that the user belongs to the customer account
    errors: list[UserNotAssociatedWithCustomerError] = validate_user_belongs_to_customer(
        order=valid_order, store=base_store
    )

    # THEN no error should be raised
    assert not errors
