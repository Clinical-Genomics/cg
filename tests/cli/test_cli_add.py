from cg.store import Store


def test_add_customer(invoke_cli, disk_store: Store):
    # GIVEN an empty database

    # WHEN adding a customer
    db_uri = disk_store.uri
    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "customer",
            "internal_id",
            "testcust",
            "--invoice-address",
            "Test adress",
            "--invoice-reference",
            "ABCDEF",
        ]
    )

    # THEN it should be stored in the database
    assert result.exit_code == 0
    assert disk_store.Customer.query.count() == 1


def test_add_user(invoke_cli, disk_store: Store):
    # GIVEN a database with a customer in it that we can connect the user to
    customer_id = "custtest"
    customer_group = disk_store.add_customer_group("dummy_group", "dummy group")
    customer = disk_store.add_customer(
        internal_id=customer_id,
        name="Test Customer",
        scout_access=False,
        customer_group=customer_group,
        invoice_address="Street nr, 12345 Uppsala",
        invoice_reference="ABCDEF",
    )
    disk_store.add_commit(customer)

    # WHEN adding a new user
    name, email = "Paul T. Anderson", "paul.anderson@magnolia.com"
    db_uri = disk_store.uri
    result = invoke_cli(["--database", db_uri, "add", "user", "-c", customer_id, email, name])

    # THEN it should be stored in the database
    assert result.exit_code == 0
    assert disk_store.User.query.count() == 1
