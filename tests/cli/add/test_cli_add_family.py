"""Tests the CLI methods to add cases to the status database."""

from click.testing import CliRunner

from cg.cli.add import add
from cg.constants import DataDelivery, Workflow
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Customer, Panel
from cg.store.store import Store
from tests.store_helpers import StoreHelpers

CLI_OPTION_ANALYSIS = Workflow.BALSAMIC_UMI
CLI_OPTION_DELIVERY = DataDelivery.FASTQ_QC


def test_add_case_required(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers, ticket_id: str
):
    """Test to add a case using only the required arguments"""
    # GIVEN a database with a customer and a panel
    disk_store: Store = base_context.status_db

    customer: Customer = helpers.ensure_customer(store=disk_store)
    customer_id = customer.internal_id
    panel: Panel = helpers.ensure_panel(store=disk_store)
    panel_id = panel.name
    name = "case-name"

    # WHEN adding a panel
    result = cli_runner.invoke(
        add,
        [
            "case",
            "--panel",
            panel_id,
            "--analysis",
            CLI_OPTION_ANALYSIS,
            "--data-delivery",
            CLI_OPTION_DELIVERY,
            "--ticket",
            ticket_id,
            customer_id,
            name,
        ],
        obj=base_context,
        input="y",
    )

    # THEN it should be added
    assert result.exit_code == 0
    case_query = disk_store._get_query(table=Case)
    assert case_query.count() == 1
    assert case_query.first().name == name
    assert case_query.first().panels == [panel_id]


def test_add_case_bad_workflow(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers, ticket_id: str
):
    """Test to add a case using only the required arguments"""
    # GIVEN a database with a customer and a panel

    # WHEN adding a case
    disk_store: Store = base_context.status_db

    customer: Customer = helpers.ensure_customer(store=disk_store)
    customer_id = customer.internal_id
    panel: Panel = helpers.ensure_panel(store=disk_store)
    panel_id = panel.name
    non_existing_analysis = "epigenentic_alterations"
    name = "case_name"

    result = cli_runner.invoke(
        add,
        [
            "case",
            "--panel",
            panel_id,
            "--analysis",
            non_existing_analysis,
            "--data-delivery",
            CLI_OPTION_DELIVERY,
            "--ticket",
            ticket_id,
            customer_id,
            name,
        ],
        input="y",
    )

    # THEN it should not be added
    assert result.exit_code != 0
    assert disk_store._get_query(table=Case).count() == 0


def test_add_case_bad_data_delivery(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers
):
    """Test to add a case using only the required arguments"""
    # GIVEN a database with a customer and an panel

    # WHEN adding a case without data delivery
    disk_store: Store = base_context.status_db

    customer: Customer = helpers.ensure_customer(store=disk_store)
    customer_id = customer.internal_id
    panel: Panel = helpers.ensure_panel(store=disk_store)
    panel_id = panel.name
    name = "case_name"
    non_existing_data_delivery = "aws"

    result = cli_runner.invoke(
        add,
        [
            "case",
            "--panel",
            panel_id,
            "--analysis",
            CLI_OPTION_ANALYSIS,
            "--data-delivery",
            non_existing_data_delivery,
            customer_id,
            name,
        ],
        obj=base_context,
        input="y",
    )

    # THEN it should not be added
    assert result.exit_code != 0
    assert disk_store._get_query(table=Case).count() == 0


def test_add_case_bad_customer(cli_runner: CliRunner, base_context: CGConfig, ticket_id: str):
    """Test to add a case using a non-existing customer"""
    # GIVEN an empty database
    disk_store: Store = base_context.status_db
    # WHEN adding a case
    panel_id = "dummy_panel"
    customer_id = "dummy_customer"
    name = "dummy_name"
    result = cli_runner.invoke(
        add,
        [
            "case",
            "--panel",
            panel_id,
            "--analysis",
            CLI_OPTION_ANALYSIS,
            "--data-delivery",
            CLI_OPTION_DELIVERY,
            "--ticket",
            ticket_id,
            customer_id,
            name,
        ],
        obj=base_context,
        input="y",
    )

    # THEN it should complain about missing customer instead of adding a case
    assert result.exit_code == 1
    assert disk_store._get_query(table=Case).count() == 0


def test_add_case_bad_panel(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers, ticket_id: str
):
    """Test to add a case using a non-existing panel"""
    # GIVEN a database with a customer
    disk_store: Store = base_context.status_db
    # WHEN adding a case
    customer: Customer = helpers.ensure_customer(store=disk_store)
    customer_id = customer.internal_id
    panel_id = "dummy_panel"
    name = "dummy_name"
    result = cli_runner.invoke(
        add,
        [
            "case",
            "--panel",
            panel_id,
            "--analysis",
            CLI_OPTION_ANALYSIS,
            "--data-delivery",
            CLI_OPTION_DELIVERY,
            "--ticket",
            ticket_id,
            customer_id,
            name,
        ],
        obj=base_context,
    )

    # THEN it should complain about missing panel instead of adding a case
    assert result.exit_code == 1
    assert disk_store._get_query(table=Case).count() == 0


def test_add_case_priority(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers, ticket_id: str
):
    """Test that the added case get the priority we send in"""
    # GIVEN a database with a customer and a panel
    disk_store: Store = base_context.status_db
    # WHEN adding a case
    customer: Customer = helpers.ensure_customer(store=disk_store)
    customer_id = customer.internal_id
    panel: Panel = helpers.ensure_panel(store=disk_store)
    panel_id = panel.name

    name = "case-name"
    priority = "priority"

    result = cli_runner.invoke(
        add,
        [
            "case",
            "--panel",
            panel_id,
            "--priority",
            priority,
            "--analysis",
            CLI_OPTION_ANALYSIS,
            "--data-delivery",
            CLI_OPTION_DELIVERY,
            "--ticket",
            ticket_id,
            customer_id,
            name,
        ],
        obj=base_context,
        input="y",
    )

    # THEN it should be added
    assert result.exit_code == 0
    case_query = disk_store._get_query(table=Case)

    assert case_query.count() == 1
    assert case_query.first().priority_human == priority
