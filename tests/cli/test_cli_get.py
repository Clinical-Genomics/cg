from cg.store import Store


def test_get_family_by_name(invoke_cli, disk_store: Store):
    # GIVEN A database with a customer in it
    customer_id = "customer-test"
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

    # WHEN trying to get a non-existing family by name
    db_uri = disk_store.uri
    result = invoke_cli(
        [
            "--database",
            db_uri,
            "get",
            "family",
            "-c",
            customer_id,
            "-n",
            "dummy-family-name",
        ]
    )

    # THEN it should not crash
    assert result.exit_code == 0
