import pytest

from cg.store.models import Customer
from cg.store.store import Store


@pytest.mark.parametrize("contact_type", ["delivery", "primary", "invoice"])
def test_contact_storing(store: Store, contact_type, helpers):
    # GIVEN an empty database
    assert store._get_query(table=Customer).first() is None
    internal_id, name, scout_access = "cust000", "Test customer", True
    contact_email = f"{contact_type}.contact@customer.se"
    contact_name = contact_type

    # WHEN adding a new customer and setting the new field
    new_customer = store.add_customer(
        internal_id=internal_id,
        name=name,
        scout_access=scout_access,
        invoice_address="dummy street 1",
        invoice_reference="dummy nr",
    )
    new_user = store.add_user(new_customer, contact_email, contact_name)

    contact_field = f"{contact_type}_contact"
    setattr(new_customer, contact_field, new_user)
    store.session.add(new_customer)
    store.session.commit()

    # THEN contact should be stored on the customer
    assert (
        getattr(store.get_customer_by_internal_id(customer_internal_id=internal_id), contact_field)
        == new_user
    )


@pytest.mark.parametrize("contact_type", ["delivery", "primary", "invoice"])
def test_contact_structure(store: Store, contact_type):
    # GIVEN the Customer model

    # WHEN checking the structure of Customer

    # THEN contact email and name should not be present
    assert not hasattr(Customer, contact_type + "_contact_email")
    assert not hasattr(Customer, contact_type + "_contact_name")

    # THEN deprecated attributes should not be present
    assert hasattr(Customer, contact_type + "_contact_id")
    assert hasattr(Customer, contact_type + "_contact")


def test_add_basic(store: Store):
    # GIVEN an empty database
    assert (store._get_query(table=Customer)).first() is None
    internal_id, name, scout_access = "cust000", "Test customer", True
    collaboration = store.add_collaboration("dummy_group", "dummy group")

    # WHEN adding a new customer
    new_customer = store.add_customer(
        internal_id=internal_id,
        name=name,
        scout_access=scout_access,
        invoice_address="dummy street 1",
        invoice_reference="dummy nr",
    )
    new_customer.collaborations.append(collaboration)
    store.session.add(new_customer)
    store.session.commit()

    # THEN it should be stored in the database
    assert (store._get_query(table=Customer)).first() == new_customer
