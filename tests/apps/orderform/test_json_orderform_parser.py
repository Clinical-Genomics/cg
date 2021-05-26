from cg.apps.orderform.json_orderform_parser import JsonOrderformParser


def test_parse_rml_orderform(rml_order_to_submit: dict):
    """Test to parse the RML orderform"""
    # GIVEN a orderform API
    order_form_parser = JsonOrderformParser()

    # WHEN parsing the RML orderform
    order_form_parser.parse_orderform(order_data=rml_order_to_submit)

    # THEN assert that the orderform was parsed in the correct way
    assert order_form_parser.order_name == rml_order_to_submit.get("name")


def test_parse_json_orderform(mip_json_orderform: dict):
    """Test to parse the RML orderform"""
    # GIVEN a orderform API
    order_form_parser = JsonOrderformParser()

    # WHEN parsing the RML orderform
    order_form_parser.parse_orderform(order_data=mip_json_orderform)

    # THEN assert that the orderform was parsed in the correct way
    assert order_form_parser.order_name == mip_json_orderform.get("name")
