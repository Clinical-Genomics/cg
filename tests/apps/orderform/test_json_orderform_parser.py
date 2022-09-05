import pytest

from cg.apps.orderform.json_orderform_parser import JsonOrderformParser
from cg.models.orders.constants import OrderType
from cg.models.orders.orderform_schema import Orderform
from tests.meta.orders.conftest import all_orders_to_submit


def test_parse_rml_orderform(rml_order_to_submit: dict):
    """Test to parse the RML orderform"""
    # GIVEN an orderform API
    order_form_parser = JsonOrderformParser()

    # WHEN parsing the RML orderform
    order_form_parser.parse_orderform(order_data=rml_order_to_submit)

    # THEN assert that the orderform was parsed in the correct way
    assert order_form_parser.order_name == rml_order_to_submit.get("name")


def test_parse_json_orderform(mip_order_to_submit: dict):
    """Test to parse the RML orderform"""
    # GIVEN an orderform API
    order_form_parser = JsonOrderformParser()

    # WHEN parsing the RML orderform
    order_form_parser.parse_orderform(order_data=mip_order_to_submit)

    # THEN assert that the orderform was parsed in the correct way
    assert order_form_parser.order_name == mip_order_to_submit.get("name")


@pytest.mark.parametrize(
    "valid_json_order_type", [OrderType.BALSAMIC, OrderType.FLUFFY, OrderType.MIP_DNA]
)
def test_generate_mip_json_orderform(valid_json_order_type: dict, all_orders_to_submit):
    """Tests the orderform generation mip-dna json files"""
    # GIVEN an orderform API

    # WHEN and orderform is parsed and an Orderform object generated
    order_form_parser = all_orders_to_submit[valid_json_order_type]
    order_form: Orderform = order_form_parser.generate_orderform()
    # THEN the created Orderform should contain cases and samples
    assert order_form.cases and order_form.samples


def test_generate_fluffy_json_orderform(fluffy_order_to_submit: dict):
    """Tests the orderform generation fluffy json files"""
    # GIVEN an orderform API
    order_form_parser = JsonOrderformParser()

    # WHEN and orderform is parsed and an Orderform object generated
    order_form_parser.parse_orderform(order_data=fluffy_order_to_submit)
    order_form: Orderform = order_form_parser.generate_orderform()
    # THEN the created Orderform should contain cases and samples
    assert order_form.cases and order_form.samples


def test_generate_balsamic_json_orderform(balsamic_order_to_submit: dict):
    """Tests the orderform generation balsamic json files"""
    # GIVEN an orderform API
    order_form_parser = JsonOrderformParser()

    # WHEN and orderform is parsed and an Orderform object generated
    order_form_parser.parse_orderform(order_data=balsamic_order_to_submit)
    order_form: Orderform = order_form_parser.generate_orderform()
    # THEN the created Orderform should contain cases and samples
    assert order_form.cases and order_form.samples
