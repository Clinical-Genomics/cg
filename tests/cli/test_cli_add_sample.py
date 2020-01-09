import datetime

from cg.store import Store


def test_add_sample_bad_customer(invoke_cli, disk_store: Store):
    # GIVEN an empty database

    # WHEN adding a sample
    db_uri = disk_store.uri
    sex = "male"
    application = "dummy_application"
    customer_id = "dummy_customer"
    name = "dummy_name"
    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "sample",
            "--sex",
            sex,
            "--application",
            application,
            customer_id,
            name,
        ]
    )

    # THEN then it should complain about missing customer instead of adding a sample
    assert result.exit_code == 1
    assert disk_store.Sample.query.count() == 0


def test_add_sample_bad_application(invoke_cli, disk_store: Store):
    # GIVEN a database with a customer

    # WHEN adding a sample
    db_uri = disk_store.uri
    sex = "male"
    application = "dummy_application"
    customer_id = add_customer(disk_store)
    name = "dummy_name"
    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "sample",
            "--sex",
            sex,
            "--application",
            application,
            customer_id,
            name,
        ]
    )

    # THEN then it should complain about missing application instead of adding a sample
    assert result.exit_code == 1
    assert disk_store.Sample.query.count() == 0


def test_add_sample_required(invoke_cli, disk_store: Store):
    # GIVEN a database with a customer and an application

    # WHEN adding a sample
    db_uri = disk_store.uri
    sex = "male"
    application = add_application(disk_store)
    customer_id = add_customer(disk_store)
    name = "sample_name"

    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "sample",
            "--sex",
            sex,
            "--application",
            application,
            customer_id,
            name,
        ]
    )

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.Sample.query.count() == 1
    assert disk_store.Sample.query.first().name == name
    assert disk_store.Sample.query.first().sex == sex


def test_add_sample_lims_id(invoke_cli, disk_store: Store):
    # GIVEN a database with a customer and an application

    # WHEN adding a sample
    db_uri = disk_store.uri
    sex = "male"
    application = add_application(disk_store)
    customer_id = add_customer(disk_store)
    name = "sample_name"
    lims_id = "sample_lims_id"

    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "sample",
            "--sex",
            sex,
            "--application",
            application,
            "--lims",
            lims_id,
            customer_id,
            name,
        ]
    )

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.Sample.query.count() == 1
    assert disk_store.Sample.query.first().internal_id == lims_id


def test_add_sample_order(invoke_cli, disk_store: Store):
    # GIVEN a database with a customer and an application

    # WHEN adding a sample
    db_uri = disk_store.uri
    sex = "male"
    application = add_application(disk_store)
    customer_id = add_customer(disk_store)
    name = "sample_name"
    order = "sample_order"

    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "sample",
            "--sex",
            sex,
            "--application",
            application,
            "--order",
            order,
            customer_id,
            name,
        ]
    )

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.Sample.query.count() == 1
    assert disk_store.Sample.query.first().order == order


def test_add_sample_downsampled(invoke_cli, disk_store: Store):
    # GIVEN a database with a customer and an application

    # WHEN adding a sample
    db_uri = disk_store.uri
    sex = "male"
    application = add_application(disk_store)
    customer_id = add_customer(disk_store)
    name = "sample_name"
    downsampled_to = "123"

    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "sample",
            "--sex",
            sex,
            "--application",
            application,
            "--downsampled",
            downsampled_to,
            customer_id,
            name,
        ]
    )

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.Sample.query.count() == 1
    assert str(disk_store.Sample.query.first().downsampled_to) == downsampled_to


def test_add_sample_priority(invoke_cli, disk_store: Store):
    # GIVEN a database with a customer and an application

    # WHEN adding a sample
    db_uri = disk_store.uri
    sex = "male"
    application = add_application(disk_store)
    customer_id = add_customer(disk_store)
    name = "sample_name"
    priority = "priority"

    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "sample",
            "--sex",
            sex,
            "--application",
            application,
            "--priority",
            priority,
            customer_id,
            name,
        ]
    )

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.Sample.query.count() == 1
    assert disk_store.Sample.query.first().priority_human == priority


def add_customer(disk_store, customer_id="cust_test"):
    customer_group = disk_store.add_customer_group("dummy_group", "dummy group")
    customer = disk_store.add_customer(
        internal_id=customer_id,
        name="Test Customer",
        scout_access=False,
        customer_group=customer_group,
        invoice_address="dummy_address",
        invoice_reference="dummy_reference",
    )
    disk_store.add_commit(customer)
    return customer_id


def add_application(disk_store, application_tag="dummy_tag"):

    application = disk_store.add_application(
        tag=application_tag,
        category="wgs",
        description="dummy_description",
        percent_kth=80,
    )
    disk_store.add_commit(application)
    prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
    version = disk_store.add_version(
        application, 1, valid_from=datetime.datetime.now(), prices=prices
    )

    disk_store.add_commit(version)
    return application_tag
