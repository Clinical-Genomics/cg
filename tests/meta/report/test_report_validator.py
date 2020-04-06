"""Tests the Validator class"""
import pytest
from cg.meta.report.report_validator import ReportValidator


@pytest.mark.parametrize(
    "required_report_value_key",
    [
        "report_version",
        "family",
        "customer_name",
        "today",
        "panels",
        "customer_invoice_address",
        "scout_access",
        "accredited",
        "pipeline_version",
        "genome_build",
    ],
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


@pytest.mark.parametrize(
    "required_sample_value_key",
    [
        "name",
        "internal_id",
        "sex",
        "status",
        # "source",
        "ticket",
        "application",
        # "received_at",
        "ordered_at",
        # "prep_method",
        # "prepared_at",
        # "capture_kit",
        # "sequencing_method",
        # "sequenced_at",
        "delivery_method",
        "delivered_at",
        # "million_read_pairs",
        # "mapped_reads",
        # "target_coverage",
        # "target_completeness",
        # "duplicates",
        "processing_time",
        "data_analysis",
        "analysis_sex",
    ],
)
def test_required_report_sample_fields_raises(report_api, report_store, required_sample_value_key):

    # GIVEN complete delivery data missing only the data we check for value on each sample
    delivery_data = report_api._get_delivery_data(family_id="yellowhog")
    assert ReportValidator(report_store).has_required_data(delivery_data)

    for sample in delivery_data["samples"]:
        sample[required_sample_value_key] = None

    # WHEN checking that the data set has the required value
    has_required_data = ReportValidator(report_store).has_required_data(delivery_data)

    # THEN the indication on completeness should be false
    assert not has_required_data


@pytest.mark.parametrize(
    "required_sample_value_key",
    [
        "received_at",
        "prep_method",
        "prepared_at",
        "sequencing_method",
        "sequenced_at",
        "million_read_pairs",
        "mapped_reads",
        "target_coverage",
        "target_completeness",
        "duplicates",
    ],
)
def test_required_sequence_sample_fields_raises(
    report_api, report_store, required_sample_value_key
):

    # GIVEN complete delivery data missing only the data we check for value on each sample
    delivery_data = report_api._get_delivery_data(family_id="yellowhog")
    assert ReportValidator(report_store).has_required_data(delivery_data)

    for sample in delivery_data["samples"]:
        assert not report_store.sample(
            sample["internal_id"]
        ).application_version.application.is_external

        sample[required_sample_value_key] = None

    # WHEN checking that the data set has the required value
    has_required_data = ReportValidator(report_store).has_required_data(delivery_data)

    # THEN the indication on completeness should be false
    assert not has_required_data
