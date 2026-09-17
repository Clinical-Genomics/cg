from unittest.mock import Mock, create_autospec

import pytest

from cg.apps.orderform.json_orderform_parser import JsonOrderformParser
from cg.models.orders.constants import OrderType
from cg.models.orders.orderform_schema import Orderform
from cg.store.models import Customer, Sample
from cg.store.store import Store


@pytest.mark.parametrize(
    "valid_json_order_type",
    [OrderType.MIP_DNA, OrderType.BALSAMIC, OrderType.FLUFFY],
)
def test_generate_json_orderform(valid_json_order_type: str, json_order_dict: dict):
    """Tests the orderform generation for customer-submitted json files"""

    # GIVEN a dictionary from a JSON file of a certain order type
    json_order: dict = json_order_dict[valid_json_order_type]

    # WHEN an orderform is parsed and an Orderform object generated
    order_form_parser = JsonOrderformParser()
    order_form_parser.parse_orderform(order_data=json_order)
    order_form: Orderform = order_form_parser.generate_orderform(create_autospec(Store))

    # THEN the created Orderform should contain samples, an order type and a delivery_type
    assert order_form.samples
    assert order_form.project_type
    assert order_form.delivery_type


def test_generate_json_orderform_with_existing_samples(mip_uploaded_json_order: dict):
    # GIVEN a JSON order containing existing samples
    existing_sample_dict = {
        "application": "WGS123",
        "cohorts": ["cohort"],
        "data_analysis": "mip-dna",
        "data_delivery": "scout",
        "existing_sample": True,
        "family_name": "case-name",
        "father": "some-father",
        "internal_id": "internal_id",
        "mother": "some-mother",
        "name": "existing-sample-name",
        "panels": ["OMIM-AUTO"],
        "subject_id": "existing-subject",
    }
    mip_uploaded_json_order["samples"].append(existing_sample_dict)

    # GIVEN that the existing sample's subject_id matches multiple samples
    status_db: Store = create_autospec(Store)
    status_db.get_customer_by_internal_id_strict = Mock(
        return_value=create_autospec(Customer, id=1)
    )
    status_db.get_samples_by_subject_id_customers_and_order_type = Mock(
        return_value=[
            create_autospec(Sample, internal_id="sample1"),
            create_autospec(Sample, internal_id="sample2"),
            create_autospec(Sample, internal_id="sample3"),
        ]
    )

    # WHEN generating the orderform
    order_form_parser = JsonOrderformParser()
    order_form_parser.parse_orderform(mip_uploaded_json_order)
    order_form: Orderform = order_form_parser.generate_orderform(status_db)

    assert order_form.samples
