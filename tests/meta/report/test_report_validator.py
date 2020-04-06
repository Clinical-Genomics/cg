"""Tests the Validator class"""
import pytest
from cg.meta.report.report_validator import ReportValidator


@pytest.mark.parametrize(
    "required_report_value_key",
    ["report_version",
     "family",
     "customer_name",
     "today",
     "panels",
     "customer_invoice_address",
     "scout_access",
     "accredited",
     ]
)
def test_required_report_fields_raises(report_api, required_report_value_key, report_store):
    # GIVEN complete delivery data missing only the data we check for value
    delivery_data = report_api._get_delivery_data(family_id="yellowhog")
    assert ReportValidator(report_store).has_required_data(delivery_data)

    delivery_data[required_report_value_key] = None

    # WHEN checking that the data set has the required value
    has_required_data = ReportValidator(report_store).has_required_data(delivery_data)

    # THEN the indication on completeness should be false
    assert not has_required_data

# @pytest.mark.parametrize(
#     "required_report_value_key",
#     ["report_version",
#      "family",
#      "customer_name",
#      "today",
#      "panels",
#      "customer_invoice_address",
#      "customer_name",
#      "scout_access",
#      "accredited",
#     ]
# )
# def test_required_report_sample_fields_raises(report_api, required_report_value_key):
#
#     # GIVEN complete delivery data missing only the data we check for value
#     delivery_data = report_api._get_delivery_data(family_id="yellowhog")
#     assert report_api._has_required_data(delivery_data)
#
#     delivery_data[required_report_value_key] = None
#
#     # WHEN checking that the data set has the required value
#     has_required_data = report_api._has_required_data(delivery_data)
#
#     # THEN the indication on completeness should be false
#     assert not has_required_data


# @pytest.mark.parametrize(
#     "required_sample_value_key",
#     ["values"]
# )
# def test_required_sample_fields_raises_on_rml(report_api, required_sample_value_key):
#     # GIVEN complete delivery data missing only the data we check for value
#     delivery_data = report_api._get_delivery_data(family_id="yellowhog")
#     assert report_api._has_required_data(delivery_data)
#
#     for sample in delivery_data["samples"]:
#         sample[required_sample_value_key] = None
#
#     # WHEN checking that the data set has the required value
#     has_required_data = report_api._has_required_data(delivery_data)
#
#     # THEN the indication on completeness should be false
#     assert not has_required_data
#
#
# @pytest.mark.parametrize(
#     "required_sample_value_key",
#     ["values"]
# )
# def test_required_sample_fields_raises_on_external(report_api, required_sample_value_key):
#     # GIVEN complete delivery data missing only the data we check for value
#     delivery_data = report_api._get_delivery_data(family_id="yellowhog")
#     assert report_api._has_required_data(delivery_data)
#
#     for sample in delivery_data["samples"]:
#         sample[required_sample_value_key] = None
#
#     # WHEN checking that the data set has the required value
#     has_required_data = report_api._has_required_data(delivery_data)
#
#     # THEN the indication on completeness should be false
#     assert not has_required_data
#
#
# @pytest.mark.parametrize(
#     "required_sample_value_key",
#     ["values"]
# )
# def test_required_sample_fields_raises_on_internal(report_api, required_sample_value_key):
#     # GIVEN complete delivery data missing only the data we check for value
#     delivery_data = report_api._get_delivery_data(family_id="yellowhog")
#     assert report_api._has_required_data(delivery_data)
#
#     for sample in delivery_data["samples"]:
#         sample[required_sample_value_key] = None
#
#     # WHEN checking that the data set has the required value
#     has_required_data = report_api._has_required_data(delivery_data)
#
#     # THEN the indication on completeness should be false
#     assert not has_required_data
