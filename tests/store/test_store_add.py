from pathlib import Path

from cg.store import Store


def test_add_customer(store: Store):
    # GIVEN an empty database
    assert store.Customer.query.first() is None
    internal_id, name, scout_access = 'cust000', 'Test customer', True
    customer_group = store.add_customer_group('dummy_group', 'dummy group')

    # WHEN adding a new customer
    new_customer = store.add_customer(internal_id=internal_id, name=name,
                                      scout_access=scout_access, customer_group=customer_group)
    store.add_commit(new_customer)

    # THEN it should be stored in the database
    assert store.Customer.query.first() == new_customer


def test_add_customer_group(store: Store):
    # GIVEN an empty database
    assert store.CustomerGroup.query.first() is None
    internal_id, name = 'cust_group', 'Test customer group'

    # WHEN adding a new customer group
    new_customer_group = store.add_customer_group(internal_id=internal_id, name=name)
    store.add_commit(new_customer_group)

    # THEN it should be stored in the database
    assert store.CustomerGroup.query.first() == new_customer_group


def test_add_user(store: Store):
    # GIVEN a database with a customer in it that we can connect the user to
    customer_group = store.add_customer_group('dummy_group', 'dummy group')
    customer = store.add_customer(internal_id='custtest', name="Test Customer",
                                  scout_access=False, customer_group=customer_group)
    store.add_commit(customer)

    # WHEN adding a new user
    name, email = 'Paul T. Anderson', 'paul.anderson@magnolia.com'
    new_user = store.add_user(customer=customer, email=email, name=name)

    # THEN it should be stored in the database
    assert store.User.query.first() == new_user
