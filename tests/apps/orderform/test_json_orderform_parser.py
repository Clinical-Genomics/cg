from unittest.mock import Mock, create_autospec

import pytest

from cg.apps.orderform.json_orderform_parser import JsonOrderformParser
from cg.exc import SubjectIdMissingError
from cg.models.orders.constants import OrderType
from cg.models.orders.orderform_schema import Orderform
from cg.models.orders.sample_base import OrderSample
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


def test_generate_json_orderform_with_existing_sample():
    # GIVEN a JSON order containing an existing sample
    existing_sample_dict = {
        "application": "WGS123",
        "cohorts": ["cohort"],
        "data_analysis": "raredisease",
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
    order = {
        "comment": "",
        "customer": "cust000",
        "name": "test-order",
        "samples": [existing_sample_dict],
    }

    # GIVEN that the existing sample's subject_id matches three samples
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
    order_form_parser.parse_orderform(order)
    order_form: Orderform = order_form_parser.generate_orderform(status_db)

    # THEN three existing samples should be in the response
    expected_sample_1 = OrderSample(
        application="WGS123",
        cohorts=["cohort"],
        customer="cust000",
        data_analysis="raredisease",
        data_delivery="scout",
        existing_sample=True,
        family_name="case-name",
        father="some-father",
        internal_id="sample1",
        mother="some-mother",
        name="existing-sample-name",
        panels=["OMIM-AUTO"],
    )
    expected_sample_2 = OrderSample(
        application="WGS123",
        cohorts=["cohort"],
        customer="cust000",
        data_analysis="raredisease",
        data_delivery="scout",
        existing_sample=True,
        family_name="case-name",
        father="some-father",
        internal_id="sample2",
        mother="some-mother",
        name="existing-sample-name",
        panels=["OMIM-AUTO"],
    )
    expected_sample_3 = OrderSample(
        application="WGS123",
        cohorts=["cohort"],
        customer="cust000",
        data_analysis="raredisease",
        data_delivery="scout",
        existing_sample=True,
        family_name="case-name",
        father="some-father",
        internal_id="sample3",
        mother="some-mother",
        name="existing-sample-name",
        panels=["OMIM-AUTO"],
    )
    assert order_form.samples == [expected_sample_1, expected_sample_2, expected_sample_3]


def test_generate_json_orderform_with_existing_sample_but_missing_subject_id():
    # GIVEN a JSON order containing an existing sample with no subject_id set
    existing_sample_dict = {
        "application": "WGS123",
        "cohorts": ["cohort"],
        "data_analysis": "raredisease",
        "data_delivery": "scout",
        "existing_sample": True,
        "family_name": "case-name",
        "father": "some-father",
        "internal_id": "internal_id",
        "mother": "some-mother",
        "name": "existing-sample-name",
        "panels": ["OMIM-AUTO"],
    }
    order = {
        "comment": "",
        "customer": "cust000",
        "name": "test-order",
        "samples": [existing_sample_dict],
    }

    # GIVEN a StatusDB
    status_db: Store = create_autospec(Store)

    # WHEN generating the orderform
    # THEN an error should be raised due to the missing subject_id
    order_form_parser = JsonOrderformParser()
    order_form_parser.parse_orderform(order)
    with pytest.raises(SubjectIdMissingError):
        order_form_parser.generate_orderform(status_db)
