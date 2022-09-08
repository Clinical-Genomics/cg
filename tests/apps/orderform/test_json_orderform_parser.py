import pytest

from cg.apps.orderform.json_orderform_parser import JsonOrderformParser
from cg.models.orders.constants import OrderType
from cg.models.orders.orderform_schema import Orderform


@pytest.mark.parametrize(
    "valid_json_order_type", [OrderType.MIP_DNA, OrderType.BALSAMIC, OrderType.FLUFFY]
)
def test_generate_mip_json_orderform(valid_json_order_type: str, json_order_list):
    """Tests the orderform generation for customer-submitted json files"""

    # GIVEN a dictionary from a JSON file of a certain order type
    json_order: dict = json_order_list[valid_json_order_type]

    # WHEN an orderform is parsed and an Orderform object generated
    order_form_parser = JsonOrderformParser()
    order_form_parser.parse_orderform(order_data=json_order)
    order_form: Orderform = order_form_parser.generate_orderform()

    # THEN the created Orderform should contain samples, an order type and a delivery_type
    assert order_form.samples
    assert order_form.project_type
    assert order_form.delivery_type
