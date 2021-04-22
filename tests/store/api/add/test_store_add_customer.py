import pytest
from cg.store import Store


@pytest.mark.parametrize("contact_type", ["delivery", "primary", "invoice"])
def test_contact_storing(store: Store, contact_type):

    # GIVEN an empty database
    assert store.Customer.query.first() is None
    internal_id, name, scout_access = "cust000", "Test customer", True
    customer_group = store.add_customer_group("dummy_group", "dummy group")
    contact_email = contact_type + ".contact@customer.se"

    # WHEN adding a new customer and setting the new field
    new_customer = store.add_customer(
        internal_id=internal_id,
        name=name,
        scout_access=scout_access,
        customer_group=customer_group,
        invoice_address="dummy street 1",
        invoice_reference="dummy nr",
    )

    contact_email_field = contact_type + "_contact_email"
    setattr(new_customer, contact_email_field, contact_email)
    store.add_commit(new_customer)

    # THEN contact email should be stored in the database
    assert getattr(store.customer(internal_id=internal_id), contact_email_field) == contact_email


@pytest.mark.parametrize("contact_type", ["delivery", "primary", "invoice"])
def test_contact_structure(store: Store, contact_type):

    # GIVEN the Customer model

    # WHEN checking the structure of Customer

    # THEN contact email should be present
    assert hasattr(store.Customer, contact_type + "_contact_email")

    # THEN deprecated attributes should not be present
    assert not hasattr(store.Customer, contact_type + "_contact_id")
    assert not hasattr(store.Customer, contact_type + "_contact")


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
