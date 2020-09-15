"""Test methods for cg/cli/set/microbial_order"""

import pytest

from cg.cli.set import microbial_order
from cg.store import Store

SUCCESS = 0


def test_invalid_order_empty_db(cli_runner, base_context):
    """Test to create an order in a empty database"""
    # GIVEN an empty database

    # WHEN running set with an order that does not exist
    order_id = "dummy_order_id"
    application_tag = "dummy_application"
    result = cli_runner.invoke(
        microbial_order, [order_id, "sign", "-a", application_tag], obj=base_context
    )

    # THEN then it should complain on invalid order
    assert result.exit_code != SUCCESS


def test_invalid_order_non_empty_db(cli_runner, base_context, base_store: Store, helpers):
    """Test to create an non existing order in a populated database"""
    # GIVEN a non empty database
    order_id = "dummy_order_id"
    helpers.ensure_microbial_order(base_store, order_id=order_id)

    non_existing_order_id = "another_order_id"

    # WHEN running set with an order that does not exist
    application_tag = "dummy_application"
    result = cli_runner.invoke(
        microbial_order,
        [non_existing_order_id, "sign", "-a", application_tag],
        obj=base_context,
    )

    # THEN then it should complain on invalid order
    assert result.exit_code != SUCCESS


def test_valid_order_no_apptag_option(cli_runner, base_context, base_store: Store, helpers):
    """Test to create an order without an apptag"""
    # GIVEN a non empty database
    order = helpers.ensure_microbial_order(base_store)

    # WHEN running set with an order that does not exist
    order_id = order.internal_id
    result = cli_runner.invoke(microbial_order, [order_id, "sign"], obj=base_context)

    # THEN then it should just exit
    assert result.exit_code != SUCCESS


@pytest.mark.parametrize("option_key", ["--name", "--ticket"])
def test_set_option(cli_runner, base_context, base_store: Store, option_key, helpers):
    """Test to set an order with an option"""

    # GIVEN a database with an order
    order = helpers.ensure_microbial_order(base_store)
    option_value = "option_value"

    # WHEN calling set_microbial_order with option
    signature = "sign"
    result = cli_runner.invoke(
        microbial_order,
        [order.internal_id, signature, option_key, option_value],
        obj=base_context,
    )

    # THEN then the option should have been set on the object and the user been informed
    assert result.exit_code == SUCCESS
    assert order.internal_id in result.output
    assert option_value in result.output
    assert option_value in base_store.MicrobialOrder.query.first().to_dict().values()
    assert signature in base_store.MicrobialOrder.query.first().comment


def test_set_project_name_in_lims(cli_runner, base_context, base_store, helpers):
    """Test to set an order with a option so that LIMS info is outputed"""

    # GIVEN a database with an order
    order = helpers.ensure_microbial_order(base_store)
    name = "a_name"

    # WHEN calling set_microbial_order with option
    signature = "sign"
    result = cli_runner.invoke(
        microbial_order,
        [order.internal_id, signature, "--name", name],
        obj=base_context,
    )

    # THEN then the option should have been set on the object and the user been informed
    assert result.exit_code == SUCCESS
    assert "LIMS" in result.output
    assert name in result.output
    assert name in base_context["lims"].get_updated_project_name()


@pytest.mark.parametrize("option_key", ["--name", "--ticket"])
def test_set_option_with_same_value(
    cli_runner, base_context, base_store: Store, option_key, helpers
):
    """Test to set an order with the same option_value twice"""

    # GIVEN a database with an order
    order = helpers.ensure_microbial_order(base_store)
    option_value = "option_value"
    first_sign = "first_sign"
    second_sign = "second_sign"

    # WHEN calling set_microbial_order with same option_value
    cli_runner.invoke(
        microbial_order,
        [order.internal_id, first_sign, option_key, option_value],
        obj=base_context,
    )
    result = cli_runner.invoke(
        microbial_order,
        [order.internal_id, second_sign, option_key, option_value],
        obj=base_context,
    )

    # THEN then the second call should not render a change in comment
    assert result.exit_code == SUCCESS
    assert order.internal_id in result.output
    assert option_value in result.output
    assert option_value in base_store.MicrobialOrder.query.first().to_dict().values()
    assert first_sign in base_store.MicrobialOrder.query.first().comment
    assert second_sign not in base_store.MicrobialOrder.query.first().comment


def test_old_comment_preserved(cli_runner, base_context, base_store: Store, helpers):
    """Test to set an order and check if old comment is preserved"""

    # GIVEN a database with an order
    order = helpers.ensure_microbial_order(base_store)
    first_sign = "first_sign"
    second_sign = "second_sign"

    # WHEN calling set_microbial_order twice with different signatures
    cli_runner.invoke(
        microbial_order,
        [order.internal_id, first_sign, "--name", "dummy_name1"],
        obj=base_context,
    )
    result = cli_runner.invoke(
        microbial_order,
        [order.internal_id, second_sign, "--name", "dummy_name2"],
        obj=base_context,
    )

    # THEN both signatures should be found in the comment
    assert result.exit_code == SUCCESS
    assert first_sign in base_store.MicrobialOrder.query.first().comment
    assert second_sign in base_store.MicrobialOrder.query.first().comment
