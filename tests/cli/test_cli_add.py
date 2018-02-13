
from cg.store import Store


def test_add_new_customer(invoke_cli, disk_store: Store):
    # GIVEN an empty database

    # WHEN adding a new customer
    db_uri = disk_store.uri
    result = invoke_cli(['--database', db_uri, 'add', 'customer', 'internal_id', 'testcust'])

    # THEN it should be stored in the database
    assert result.exit_code == 0
    assert disk_store.Customer.query.count() == 1


def test_add_user(invoke_cli, disk_store: Store):
    # GIVEN a database with a customer in it that we can connect the user to
    customer_id = 'custtest'
    customer = disk_store.add_customer(internal_id=customer_id, name="Test Customer", scout_access=False)
    disk_store.add_commit(customer)

    # WHEN adding a new user
    name, email = 'Paul T. Anderson', 'paul.anderson@magnolia.com'
    db_uri = disk_store.uri
    result = invoke_cli(['--database', db_uri, 'add', 'user', '-c', customer_id, email, name])

    # THEN it should be stored in the database
    assert result.exit_code == 0
    assert disk_store.User.query.count() == 1
