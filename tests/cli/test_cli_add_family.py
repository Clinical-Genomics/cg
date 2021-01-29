"""This script tests the cli methods to add families to status-db"""
from datetime import datetime

import click
from cg.constants import Pipeline, DataDelivery
from cg.store import Store

CLI_OPTION_ANALYSIS = Pipeline.BALSAMIC
CLI_OPTION_DELIVERY = DataDelivery.FASTQ_QC


def test_add_family_required(invoke_cli, disk_store: Store):
    """Test to add a case using only the required arguments"""
    # GIVEN a database with a customer and an panel

    # WHEN adding a case
    db_uri = disk_store.uri
    customer_id = add_customer(disk_store)
    panel_id = add_panel(disk_store)
    name = "case_name"

    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "family",
            "--panel",
            panel_id,
            "--analysis",
            CLI_OPTION_ANALYSIS,
            "--data-delivery",
            CLI_OPTION_DELIVERY,
            customer_id,
            name,
        ]
    )

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.Family.query.count() == 1
    assert disk_store.Family.query.first().name == name
    assert disk_store.Family.query.first().panels == [panel_id]


def test_add_family_bad_pipeline(invoke_cli, disk_store: Store):
    """Test to add a case using only the required arguments"""
    # GIVEN a database with a customer and an panel

    # WHEN adding a case
    db_uri = disk_store.uri
    customer_id = add_customer(disk_store)
    panel_id = add_panel(disk_store)
    non_existing_analysis = "epigenentic_alterations"
    name = "case_name"

    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "case",
            "--panel",
            panel_id,
            "--analysis",
            non_existing_analysis,
            "--data-delivery",
            CLI_OPTION_DELIVERY,
            customer_id,
            name,
        ]
    )

    # THEN then it should not be added
    assert result.exit_code != 0
    assert disk_store.Family.query.count() == 0


def test_add_family_bad_data_delivery(invoke_cli, disk_store: Store):
    """Test to add a case using only the required arguments"""
    # GIVEN a database with a customer and an panel

    # WHEN adding a case without data delivery
    db_uri = disk_store.uri
    customer_id = add_customer(disk_store)
    panel_id = add_panel(disk_store)
    non_existing_data_delivery = "aws"
    name = "case_name"

    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "case",
            "--panel",
            panel_id,
            "--analysis",
            CLI_OPTION_ANALYSIS,
            "--data-delivery",
            non_existing_data_delivery,
            customer_id,
            name,
        ]
    )

    # THEN then it should not be added
    assert result.exit_code != 0
    assert disk_store.Family.query.count() == 0


def test_add_family_bad_customer(invoke_cli, disk_store: Store):
    """Test to add a case using a non-existing customer"""
    # GIVEN an empty database

    # WHEN adding a case
    db_uri = disk_store.uri
    panel_id = "dummy_panel"
    customer_id = "dummy_customer"
    name = "dummy_name"
    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "family",
            "--panel",
            panel_id,
            "--analysis",
            CLI_OPTION_ANALYSIS,
            "--data-delivery",
            CLI_OPTION_DELIVERY,
            customer_id,
            name,
        ]
    )

    # THEN then it should complain about missing customer instead of adding a case
    assert result.exit_code == 1
    assert disk_store.Family.query.count() == 0


def test_add_family_bad_panel(invoke_cli, disk_store: Store):
    """Test to add a case using a non-existing panel"""
    # GIVEN a database with a customer

    # WHEN adding a case
    db_uri = disk_store.uri
    panel_id = "dummy_panel"
    customer_id = add_customer(disk_store)
    name = "dummy_name"
    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "family",
            "--panel",
            panel_id,
            "--analysis",
            CLI_OPTION_ANALYSIS,
            "--data-delivery",
            CLI_OPTION_DELIVERY,
            customer_id,
            name,
        ]
    )

    # THEN then it should complain about missing panel instead of adding a case
    assert result.exit_code == 1
    assert disk_store.Family.query.count() == 0


def test_add_family_priority(invoke_cli, disk_store: Store):
    """Test that the added case get the priority we send in"""
    # GIVEN a database with a customer and an panel

    # WHEN adding a case
    db_uri = disk_store.uri

    customer_id = add_customer(disk_store)
    panel_id = add_panel(disk_store)
    name = "case_name"
    priority = "priority"

    result = invoke_cli(
        [
            "--database",
            db_uri,
            "add",
            "family",
            "--panel",
            panel_id,
            "--priority",
            priority,
            "--analysis",
            CLI_OPTION_ANALYSIS,
            "--data-delivery",
            CLI_OPTION_DELIVERY,
            customer_id,
            name,
        ]
    )

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.Family.query.count() == 1
    assert disk_store.Family.query.first().priority_human == priority


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


def add_panel(disk_store, panel_id="panel_test", customer_id="cust_test"):
    """utility function to add a panel to use in tests"""
    customer = disk_store.customer(customer_id)
    panel = disk_store.add_panel(
        customer=customer,
        name=panel_id,
        abbrev=panel_id,
        version=1.0,
        date=datetime.now(),
        genes=1,
    )
    disk_store.add_commit(panel)
    return panel_id


def add_application(disk_store, application_tag="dummy_tag"):
    """utility function to add an application to use in tests"""
    application = disk_store.add_application(
        tag=application_tag,
        category="wgs",
        description="dummy_description",
        percent_kth=80,
        percent_reads_guaranteed=75,
    )
    disk_store.add_commit(application)
    prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
    version = disk_store.add_version(application, 1, valid_from=datetime.now(), prices=prices)

    disk_store.add_commit(version)
    return application_tag
