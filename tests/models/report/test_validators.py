"""Tests delivery report models validators."""
from cg.constants import NA_FIELD, YES_FIELD, REPORT_GENDER, Pipeline
from cg.constants.subject import Gender
from cg.models.orders.constants import OrderType
from cg.models.report.validators import (
    validate_empty_field,
    validate_boolean,
    validate_float,
    validate_list,
    validate_rml_sample,
    validate_supported_pipeline,
    validate_gender,
    validate_percentage,
)


def test_validate_empty_field():
    """Tests formatting an empty value."""

    # GIVEN a not valid empty field
    none_field = None

    # WHEN performing the validation
    output = validate_empty_field(none_field)

    # THEN check if the input value was formatted correctly
    assert output == NA_FIELD


def test_validate_boolean():
    """Tests boolean formatting for the delivery report."""

    # GIVEN a not formatted inputs
    none_field = None
    true_field = True
    not_bool_field = "not a boolean"

    # WHEN performing the validation
    validated_none_field = validate_boolean(none_field)
    validated_true_field = validate_boolean(true_field)
    validated_not_bool_field = validate_boolean(not_bool_field)

    # THEN check if the input values were formatted correctly
    assert validated_none_field == NA_FIELD
    assert validated_true_field == YES_FIELD
    assert validated_not_bool_field == NA_FIELD


def test_validate_float():
    """Tests the validation of a float value."""

    # GIVEN a valid float input (float and string format)
    float_value = 12.3456789
    str_value = "12.3456789"

    # WHEN performing the validation
    validated_float_value = validate_float(float_value)
    validated_str_value = validate_float(str_value)

    # THEN check if the input values were formatted correctly
    assert validated_float_value == "12.35"
    assert validated_str_value == "12.35"


def test_validate_float_zero_input():
    """Tests the validation of a float value."""

    # GIVEN a valid float input (float and string format)
    float_value = 0.0
    str_value = "0.0"

    # WHEN performing the validation
    validated_float_value = validate_float(float_value)
    validated_str_value = validate_float(str_value)

    # THEN check if the input values were formatted correctly
    assert validated_float_value == "0.0"
    assert validated_str_value == "0.0"


def test_validate_percentage():
    """Tests the validation of a percentage value."""

    # GIVEN a not formatted percentage
    pct_value = 0.9876

    # WHEN performing the validation
    validated_pct_value = validate_percentage(pct_value)

    # THEN check if the input values were formatted correctly
    assert validated_pct_value == "98.76"


def test_validate_list():
    """Tests if a list is transformed into a string of comma separated values."""

    # GIVEN a mock list
    mock_list = ["I'm", "a", "list"]

    # WHEN performing the validation
    validated_list = validate_list(mock_list)

    # THEN check if the input values were formatted correctly
    assert validated_list == "I'm, a, list"


def test_validate_rml_sample(caplog):
    """Performs validation on a preparation category."""

    # GIVEN an invalid prep category
    prep_category = OrderType.RML

    # WHEN performing the validation
    try:
        validate_rml_sample(prep_category)
        assert False
    # THEN check if an exception was raised
    except ValueError:
        assert "The delivery report generation does not support RML samples" in caplog.text


def test_validate_gender(caplog):
    """Tests report gender parsing."""

    # GIVEN an invalid gender category
    gender = Gender.FEMALE
    invalid_gender = "not_a_gender"

    # WHEN performing the validation
    validated_gender = validate_gender(gender)
    validated_invalid_gender = validate_gender(invalid_gender)

    # THEN check if the gender has been correctly formatted
    assert validated_gender == REPORT_GENDER.get("female")
    assert validated_invalid_gender == NA_FIELD


def test_validate_supported_pipeline_match_error(caplog):
    """Tests if a customer requested pipeline matches the data analysis one."""

    # GIVEN an input dictionary where the customers and executed pipeline are different
    dict_different_pipelines = {"customer_pipeline": Pipeline.MIP_DNA, "pipeline": Pipeline.FLUFFY}

    # WHEN performing the validation
    try:
        validate_supported_pipeline(None, dict_different_pipelines)
        assert False
    # THEN check if an exception was raised
    except ValueError:
        assert (
            f"The analysis requested by the customer ({dict_different_pipelines.get('customer_pipeline')}) does not "
            f"match the one executed ({dict_different_pipelines.get('pipeline')})" in caplog.text
        )


def test_validate_supported_pipeline(caplog):
    """Tests that the analysis pipeline is supported by the delivery report workflow."""

    # GIVEN a dictionary with a not supported pipeline
    dict_invalid_pipeline = {"customer_pipeline": Pipeline.FLUFFY, "pipeline": Pipeline.FLUFFY}

    # WHEN performing the validation
    try:
        validate_supported_pipeline(None, dict_invalid_pipeline)
        assert False
    # THEN check if an exception was raised
    except ValueError:
        assert (
            f"The pipeline {dict_invalid_pipeline.get('pipeline')} does not support delivery report generation"
            in caplog.text
        )
