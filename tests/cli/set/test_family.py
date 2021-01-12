"""This script tests the cli methods to set families to status-db"""

from cg.cli.set.family import family
from cg.constants import DataDelivery, Pipeline
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


def test_set_family_bad_data_analysis(cli_runner, base_context, base_store: Store, helpers):
    """Test to set a family using a non-existing data_analysis"""
    # GIVEN a database with a family

    # WHEN setting a data_analysis on a family
    data_analysis = "dummy_pipeline"
    family_id = helpers.add_family(base_store).internal_id
    result = cli_runner.invoke(
        family, [family_id, "--data-analysis", data_analysis], obj=base_context
    )

    # THEN then it should complain in non valid data_analysis instead of setting a value
    assert result.exit_code != SUCCESS
    assert str(data_analysis) != base_store.Family.query.first().data_analysis


def test_set_family_data_analysis(cli_runner, base_context, base_store: Store, helpers):
    """Test to set a family using an existing data_analysis"""

    # GIVEN a database with a family and a data_analysis not yet set on the case
    data_analysis = Pipeline.FASTQ
    case_obj = helpers.add_family(base_store)
    assert str(data_analysis) != case_obj.data_analysis

    # WHEN setting a data_analysis of a case
    result = cli_runner.invoke(
        family,
        [case_obj.internal_id, "--data-analysis", str(data_analysis)],
        obj=base_context,
        catch_exceptions=False,
    )

    # THEN then it should set data_analysis on the case
    assert result.exit_code == SUCCESS
    assert str(data_analysis) == case_obj.data_analysis


def test_set_family_bad_data_delivery(cli_runner, base_context, base_store: Store, helpers):
    """Test to set a family using a non-existing data_delivery"""
    # GIVEN a database with a family

    # WHEN setting a data_delivery on a family
    data_delivery = "dummy_delivery"
    family_id = helpers.add_family(base_store).internal_id
    result = cli_runner.invoke(
        family, [family_id, "--data-delivery", data_delivery], obj=base_context
    )

    # THEN then it should complain in non valid data_delivery instead of setting a value
    assert result.exit_code != SUCCESS
    assert str(data_delivery) != base_store.Family.query.first().data_delivery


def test_set_family_data_delivery(cli_runner, base_context, base_store: Store, helpers):
    """Test to set a family using an existing data_delivery"""

    # GIVEN a database with a family and a data_delivery not yet set on the case
    data_delivery = DataDelivery.FASTQ
    case_obj = helpers.add_family(base_store)
    assert str(data_delivery) != case_obj.data_delivery

    # WHEN setting a data_delivery of a case
    result = cli_runner.invoke(
        family,
        [case_obj.internal_id, "--data-delivery", str(data_delivery)],
        obj=base_context,
        catch_exceptions=False,
    )

    # THEN then it should set data_delivery on the case
    assert result.exit_code == SUCCESS
    assert str(data_delivery) == case_obj.data_delivery
