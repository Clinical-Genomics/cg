"""This script tests the cli methods to set values of a case in status-db."""

from click.testing import CliRunner

from cg.cli.set.case import set_case
from cg.constants import EXIT_SUCCESS, DataDelivery, Workflow
from cg.models.cg_config import CGConfig
from cg.store.models import Case
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_set_case_without_options(
    cli_runner: CliRunner,
    base_context: CGConfig,
    base_store: Store,
    helpers: StoreHelpers,
):
    """Test to set a case using only the required arguments."""
    # GIVEN a database with a case
    case_id: str = helpers.add_case(store=base_store).internal_id
    assert base_store._get_query(table=Case).count() == 1

    # WHEN setting a case
    result = cli_runner.invoke(set_case, [case_id], obj=base_context)

    # THEN it should abort
    assert result.exit_code != EXIT_SUCCESS


def test_set_case_bad_family(
    cli_runner: CliRunner, base_context: CGConfig, case_id_does_not_exist: str
):
    """Test to set a case using a non-existing case id."""
    # GIVEN an empty database

    # WHEN setting a case
    result = cli_runner.invoke(set_case, [case_id_does_not_exist], obj=base_context)

    # THEN it should complain on missing case
    assert result.exit_code != EXIT_SUCCESS


def test_set_case_bad_panel(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers: StoreHelpers
):
    """Test to set a case using a non-existing panel."""
    # GIVEN a database with a case

    # WHEN setting a case
    panel_id: str = "dummy_panel"
    case_id: str = helpers.add_case(store=base_store).internal_id
    result = cli_runner.invoke(set_case, [case_id, "--panel", panel_id], obj=base_context)

    # THEN it should complain in missing panel instead of setting a value
    assert result.exit_code != EXIT_SUCCESS
    assert panel_id not in base_store._get_query(table=Case).first().panels


def test_set_case_panel(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers: StoreHelpers
):
    """Test to set a case using an existing panel."""
    # GIVEN a database with a case and a panel not yet added to the case
    panel_id: str = helpers.ensure_panel(store=base_store, panel_abbreviation="a_panel").name
    case_id: str = helpers.add_case(store=base_store).internal_id
    case_query = base_store._get_query(table=Case)

    assert panel_id not in case_query.first().panels

    # WHEN setting a panel of a case
    result = cli_runner.invoke(set_case, [case_id, "--panel", panel_id], obj=base_context)

    # THEN it should set panel on the case
    assert result.exit_code == EXIT_SUCCESS
    assert panel_id in case_query.first().panels


def test_set_case_priority(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers: StoreHelpers
):
    """Test that the added case gets the priority we send in."""
    # GIVEN a database with a case
    case_id: str = helpers.add_case(base_store).internal_id
    priority: str = "priority"
    case_query = base_store._get_query(table=Case)

    assert case_query.first().priority_human != priority

    # WHEN setting a case
    result = cli_runner.invoke(
        set_case, [case_id, "--priority", priority], obj=base_context, catch_exceptions=False
    )

    # THEN it should have been set
    assert result.exit_code == EXIT_SUCCESS
    assert case_query.count() == 1
    assert case_query.first().priority_human == priority


def test_set_case_customer(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers: StoreHelpers
):
    """Test to set a case using an existing customer."""
    # GIVEN a database with a case and a customer not yet on the case
    customer_id: str = helpers.ensure_customer(
        store=base_store, customer_id="a_customer"
    ).internal_id
    case_to_alter: Case = helpers.add_case(store=base_store)
    assert customer_id != case_to_alter.customer.internal_id

    # WHEN setting a customer of a case
    result = cli_runner.invoke(
        set_case, [case_to_alter.internal_id, "--customer-id", customer_id], obj=base_context
    )

    # THEN it should set customer on the case
    assert result.exit_code == EXIT_SUCCESS
    assert customer_id == case_to_alter.customer.internal_id


def test_set_case_bad_data_analysis(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers: StoreHelpers
):
    """Test to set a case using a non-existing data_analysis."""
    # GIVEN a database with a case

    # WHEN setting a data_analysis on a case
    data_analysis: str = "dummy_workflow"
    case_id: str = helpers.add_case(store=base_store).internal_id
    result = cli_runner.invoke(
        set_case, [case_id, "--data-analysis", data_analysis], obj=base_context
    )

    # THEN it should complain in invalid data_analysis instead of setting a value
    assert result.exit_code != EXIT_SUCCESS
    assert str(data_analysis) != base_store._get_query(table=Case).first().data_analysis


def test_set_case_data_analysis(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers: StoreHelpers
):
    """Test to set a case using an existing data_analysis."""

    # GIVEN a database with a case and a data_analysis not yet set on the case
    data_analysis: str = Workflow.FASTQ
    case_to_alter: str = helpers.add_case(base_store)
    assert str(data_analysis) != case_to_alter.data_analysis

    # WHEN setting a data_analysis of a case
    result = cli_runner.invoke(
        set_case,
        [case_to_alter.internal_id, "--data-analysis", str(data_analysis)],
        obj=base_context,
    )

    # THEN it should set data_analysis on the case
    assert result.exit_code == EXIT_SUCCESS
    assert str(data_analysis) == case_to_alter.data_analysis


def test_set_case_bad_data_delivery(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers: StoreHelpers
):
    """Test to set a case using a non-existing data_delivery."""
    # GIVEN a database with a case

    # WHEN setting a data_delivery on a case
    data_delivery: str = "dummy_delivery"
    case_id: str = helpers.add_case(base_store).internal_id
    result = cli_runner.invoke(
        set_case, [case_id, "--data-delivery", data_delivery], obj=base_context
    )

    # THEN it should complain in invalid data_delivery instead of setting a value
    assert result.exit_code != EXIT_SUCCESS
    assert str(data_delivery) != base_store._get_query(table=Case).first().data_delivery


def test_set_case_data_delivery(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers: StoreHelpers
):
    """Test to set a case using an existing data_delivery."""

    # GIVEN a database with a case and a data_delivery not yet set on the case
    data_delivery: str = DataDelivery.FASTQ
    case_to_alter: str = helpers.add_case(base_store)
    assert str(data_delivery) != case_to_alter.data_delivery

    # WHEN setting a data_delivery of a case
    result = cli_runner.invoke(
        set_case,
        [case_to_alter.internal_id, "--data-delivery", str(data_delivery)],
        obj=base_context,
    )

    # THEN it should set data_delivery on the case
    assert result.exit_code == EXIT_SUCCESS
    assert str(data_delivery) == case_to_alter.data_delivery
