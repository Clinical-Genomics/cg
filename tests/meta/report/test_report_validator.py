"""Tests the Validator class"""
import pytest
from cg.constants import Pipeline
from cg.meta.report.report_validator import ReportValidator

NON_REQUIRED_FIELDS_ON_ALL_SAMPLES = ["source", "data_analysis"]

NON_REQUIRED_FIELDS_ON_EXTERNAL_SAMPLES = [
    "million_read_pairs",
    "prepared_at",
    "prep_method",
    "sequencing_method",
    "sequenced_at",
]

REQUIRED_SEQUENCED_SAMPLE_FIELDS = [
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
]

REQUIRED_ANALYSIS_SAMPLE_FIELDS = [
    "mapped_reads",
    "duplicates",
    "analysis_sex",
    "target_coverage",
    "target_completeness",
]

REQUIRED_REPORT_FIELDS = [
    "report_version",
    "case",
    "customer_name",
    "today",
    "panels",
    "customer_invoice_address",
    "scout_access",
    "accredited",
    "pipeline",
    "pipeline_version",
    "genome_build",
]

REQUIRED_GENERIC_SAMPLE_FIELDS = [
    "name",
    "internal_id",
    "sex",
    "status",
    "ticket",
    "application",
    "ordered_at",
    "received_at",
    "delivered_at",
    "processing_time",
    "analysis_sex",
]


@pytest.mark.parametrize("required_report_value_key", REQUIRED_REPORT_FIELDS)
def test_has_required_data_w_report_fields(report_api, required_report_value_key, report_store):
    # GIVEN complete delivery data missing only the data we check for valu
    case_id = "yellowhog"
    delivery_data = report_api._get_delivery_data(case_id=case_id)
    validator = ReportValidator(report_store)
    validator.has_required_data(delivery_data, case_id)
    assert not validator.get_missing_attributes()

    delivery_data[required_report_value_key] = None

    # WHEN checking that the data set has the required value
    has_required_data = validator.has_required_data(delivery_data, case_id)

    # THEN the indication on completeness should be false
    assert not has_required_data


@pytest.mark.parametrize("required_report_value_key", REQUIRED_REPORT_FIELDS)
def test_get_missing_data_w_report_fields(report_api, required_report_value_key, report_store):
    # GIVEN complete delivery data missing only the data we check for value
    case_id = "yellowhog"
    delivery_data = report_api._get_delivery_data(case_id=case_id)
    validator = ReportValidator(report_store)
    assert validator.has_required_data(delivery_data, case_id)
    assert required_report_value_key not in validator.get_missing_attributes()

    delivery_data[required_report_value_key] = None
    validator.has_required_data(delivery_data, case_id)

    # WHEN getting missing attributes
    missing_attributes = validator.get_missing_attributes()

    # THEN the tested attribute should be one of the missing ones
    assert required_report_value_key in missing_attributes


@pytest.mark.parametrize("required_sample_value_key", REQUIRED_GENERIC_SAMPLE_FIELDS)
def test_has_required_data_w_normal_sample_fields(
    report_api, report_store, required_sample_value_key
):
    # GIVEN complete delivery data missing only the data we check for value on each sample
    case_id = "yellowhog"
    delivery_data = report_api._get_delivery_data(case_id=case_id)
    validator = ReportValidator(report_store)
    assert validator.has_required_data(delivery_data, case_id)
    assert required_sample_value_key not in validator.get_missing_attributes()

    for sample in delivery_data["samples"]:
        sample[required_sample_value_key] = None

    # WHEN checking that the data set has the required value
    has_required_data = validator.has_required_data(delivery_data, case_id)

    # THEN the indication on completeness should be false
    assert not has_required_data


@pytest.mark.parametrize("required_sample_value_key", REQUIRED_SEQUENCED_SAMPLE_FIELDS)
def test_has_required_data_w_sequence_sample_fields(
    report_api, report_store, required_sample_value_key
):
    # GIVEN complete delivery data missing only the data we check for value on each non external
    # sample
    case_id = "yellowhog"
    delivery_data = report_api._get_delivery_data(case_id=case_id)

    for sample in delivery_data["samples"]:
        assert not report_store.sample(
            sample["internal_id"]
        ).application_version.application.is_external

    validator = ReportValidator(report_store)
    assert validator.has_required_data(delivery_data, case_id)
    assert required_sample_value_key not in validator.get_missing_attributes()

    for sample in delivery_data["samples"]:
        sample[required_sample_value_key] = None

    # WHEN checking that the data set has the required value
    has_required_data = validator.has_required_data(delivery_data, case_id)

    # THEN the indication on completeness should be false
    assert not has_required_data


@pytest.mark.parametrize("required_sample_value_key", REQUIRED_ANALYSIS_SAMPLE_FIELDS)
def test_has_required_data_w_analysis_sample_fields(
    report_api, report_store, required_sample_value_key
):
    # GIVEN complete delivery data missing only the data we check for value on each non external
    # sample
    case_id = "yellowhog"
    delivery_data = report_api._get_delivery_data(case_id=case_id)
    for sample in delivery_data["samples"]:
        report_store.sample(sample["internal_id"]).data_analysis = str(Pipeline.MIP_DNA)
    report_store.commit()

    validator = ReportValidator(report_store)
    assert validator.has_required_data(delivery_data, case_id)
    assert required_sample_value_key not in validator.get_missing_attributes()

    for sample in delivery_data["samples"]:
        sample[required_sample_value_key] = None

    # WHEN checking that the data set has the required value
    has_required_data = validator.has_required_data(delivery_data, case_id)

    # THEN the indication on completeness should be false
    assert not has_required_data


@pytest.mark.parametrize("required_sample_value_key", NON_REQUIRED_FIELDS_ON_ALL_SAMPLES)
def test_has_required_data_all_samples_non_required_fields(
    report_api, report_store, required_sample_value_key
):
    # GIVEN complete delivery data missing only the data we check for value on each sample
    case_id = "yellowhog"
    delivery_data = report_api._get_delivery_data(case_id=case_id)

    validator = ReportValidator(report_store)
    assert validator.has_required_data(delivery_data, case_id)
    assert required_sample_value_key not in validator.get_missing_attributes()

    for sample in delivery_data["samples"]:
        sample[required_sample_value_key] = None

    # WHEN checking that the data set has the required value
    has_required_data = validator.has_required_data(delivery_data, case_id)

    # THEN the indication on completeness should be true
    assert required_sample_value_key not in validator.get_missing_attributes()
    assert has_required_data


@pytest.mark.parametrize("required_sample_value_key", NON_REQUIRED_FIELDS_ON_EXTERNAL_SAMPLES)
def test_has_required_data_external_samples_non_required_fields(
    report_api, report_store, required_sample_value_key
):
    # GIVEN complete delivery data missing only the data we check for value on each external sample
    case_id = "yellowhog"
    delivery_data = report_api._get_delivery_data(case_id=case_id)
    for sample in delivery_data["samples"]:
        report_store.sample(
            sample["internal_id"]
        ).application_version.application.is_external = True
    report_store.commit()

    for sample in delivery_data["samples"]:
        assert report_store.sample(
            sample["internal_id"]
        ).application_version.application.is_external

    validator = ReportValidator(report_store)
    assert validator.has_required_data(delivery_data, case_id)
    assert required_sample_value_key not in validator.get_missing_attributes()

    for sample in delivery_data["samples"]:
        sample[required_sample_value_key] = None

    # WHEN checking that the data set has the required value
    has_required_data = validator.has_required_data(delivery_data, case_id)

    # THEN the indication on completeness should be true
    assert required_sample_value_key not in validator.get_missing_attributes()
    assert has_required_data
