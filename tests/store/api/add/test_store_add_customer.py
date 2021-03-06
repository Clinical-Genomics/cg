import pytest
from cg.store import Store


@pytest.mark.parametrize("contact_type", ["delivery", "primary", "invoice"])
def test_contact_storing(store: Store, contact_type, helpers):

    # GIVEN an empty database
    assert store.Customer.query.first() is None
    internal_id, name, scout_access = "cust000", "Test customer", True
    customer_group = store.add_customer_group("dummy_group", "dummy group")
    contact_email = contact_type + ".contact@customer.se"
    contact_name = contact_type

    # WHEN adding a new customer and setting the new field
    new_customer = store.add_customer(
        internal_id=internal_id,
        name=name,
        scout_access=scout_access,
        customer_group=customer_group,
        invoice_address="dummy street 1",
        invoice_reference="dummy nr",
    )

    new_user = store.add_user(new_customer, contact_email, contact_name)

    contact_field = contact_type + "_contact"
    setattr(new_customer, contact_field, new_user)
    store.add_commit(new_customer)

    # THEN contact should be stored on the customer
    assert getattr(store.customer(internal_id=internal_id), contact_field) == new_user


@pytest.mark.parametrize("contact_type", ["delivery", "primary", "invoice"])
def test_contact_structure(store: Store, contact_type):

    # GIVEN the Customer model

    # WHEN checking the structure of Customer

    # THEN contact email and name should not be present
    assert not hasattr(store.Customer, contact_type + "_contact_email")
    assert not hasattr(store.Customer, contact_type + "_contact_name")

    # THEN deprecated attributes should not be present
    assert hasattr(store.Customer, contact_type + "_contact_id")
    assert hasattr(store.Customer, contact_type + "_contact")


def test_add_basic(store: Store):
    # GIVEN an empty database
    assert store.Customer.query.first() is None
    internal_id, name, scout_access = "cust000", "Test customer", True
    customer_group = store.add_customer_group("dummy_group", "dummy group")

    # WHEN adding a new customer
    new_customer = store.add_customer(
        internal_id=internal_id,
        name=name,
        scout_access=scout_access,
        customer_group=customer_group,
        invoice_address="dummy street 1",
        invoice_reference="dummy nr",
    )
    store.add_commit(new_customer)

    # THEN it should be stored in the database
    assert store.Customer.query.first() == new_customer
