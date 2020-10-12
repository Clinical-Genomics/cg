"""This script tests the cli methods to set families to status-db"""

from cg.cli.set.family import family
from cg.store import Store

SUCCESS = 0


def test_set_family_without_options(cli_runner, base_context, base_store: Store, helpers):
    """Test to set a family using only the required arguments"""
    # GIVEN a database with a family
    family_id = helpers.add_family(base_store).internal_id
    assert base_store.Family.query.count() == 1

    # WHEN setting a family
    result = cli_runner.invoke(family, [family_id], obj=base_context)

    # THEN then it should abort
    assert result.exit_code != SUCCESS


def test_set_family_bad_family(cli_runner, base_context):
    """Test to set a family using a non-existing family """
    # GIVEN an empty database

    # WHEN setting a family
    family_id = "dummy_name"
    result = cli_runner.invoke(family, [family_id], obj=base_context)

    # THEN then it should complain on missing family
    assert result.exit_code != SUCCESS


def test_set_family_bad_panel(cli_runner, base_context, base_store: Store, helpers):
    """Test to set a family using a non-existing panel"""
    # GIVEN a database with a family

    # WHEN setting a family
    panel_id = "dummy_panel"
    family_id = helpers.add_family(base_store).internal_id
    result = cli_runner.invoke(family, [family_id, "--panel", panel_id], obj=base_context)

    # THEN then it should complain in missing panel instead of setting a value
    assert result.exit_code != SUCCESS
    assert panel_id not in base_store.Family.query.first().panels


def test_set_family_panel(cli_runner, base_context, base_store: Store, helpers):
    """Test to set a family using an existing panel"""
    # GIVEN a database with a family and a panel not yet added to the family
    panel_id = helpers.ensure_panel(base_store, "a_panel").name
    family_id = helpers.add_family(base_store).internal_id
    assert panel_id not in base_store.Family.query.first().panels

    # WHEN setting a panel of a family
    result = cli_runner.invoke(family, [family_id, "--panel", panel_id], obj=base_context)

    # THEN then it should set panel on the family
    assert result.exit_code == SUCCESS
    assert panel_id in base_store.Family.query.first().panels


def test_set_family_priority(cli_runner, base_context, base_store: Store, helpers):
    """Test that the added family gets the priority we send in"""
    # GIVEN a database with a family
    family_id = helpers.add_family(base_store).internal_id
    priority = "priority"
    assert base_store.Family.query.first().priority_human != priority

    # WHEN setting a family

    result = cli_runner.invoke(family, [family_id, "--priority", priority], obj=base_context)

    # THEN then it should have been set
    assert result.exit_code == SUCCESS
    assert base_store.Family.query.count() == 1
    assert base_store.Family.query.first().priority_human == priority


def test_set_family_customer(cli_runner, base_context, base_store: Store, helpers):
    """Test to set a family using an existing customer"""
    # GIVEN a database with a family and a customer not yet on the family
    customer_id = helpers.ensure_customer(base_store, customer_id="a_customer").internal_id
    case = helpers.add_family(base_store)
    assert customer_id != case.customer.internal_id

    # WHEN setting a customer of a family
    result = cli_runner.invoke(
        family, [case.internal_id, "--customer-id", customer_id], obj=base_context
    )

    # THEN then it should set customer on the family
    assert result.exit_code == SUCCESS
    assert customer_id == case.customer.internal_id
