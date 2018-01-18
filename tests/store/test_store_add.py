from pathlib import Path

from cg.store import Store


def test_add_customer(store: Store):
    # GIVEN an empty database
    assert store.Customer.query.first() is None
    internal_id, name, scout_access = 'cust000', 'Test customer', True

    # WHEN adding a new user
    new_customer = store.add_customer(internal_id=internal_id, name=name, scout_access=scout_access)
    store.add_commit(new_customer)

    # THEN it should be stored in the database
    assert store.Customer.query.first() == new_customer


def test_add_user(store: Store):
    # GIVEN a database with a customer in it that we can connect the user to
    customer = store.add_customer(internal_id='custtest', name="Test Customer", scout_access=False)
    store.add_commit(customer)

    # WHEN adding a new user
    name, email = 'Paul T. Anderson', 'paul.anderson@magnolia.com'
    new_user = store.add_user(customer=customer, email=email, name=name)

    # THEN it should be stored in the database
    assert store.User.query.first() == new_user
