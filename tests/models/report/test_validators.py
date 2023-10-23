"""Tests delivery report models validators."""
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from _pytest.logging import LogCaptureFixture
from pydantic import ValidationInfo

from cg.constants import NA_FIELD, NO_FIELD, REPORT_GENDER, YES_FIELD, Pipeline
from cg.constants.constants import AnalysisType
from cg.constants.subject import Gender
from cg.models.orders.constants import OrderType
from cg.models.report.validators import (
    get_analysis_type_as_string,
    get_boolean_as_string,
    get_date_as_string,
    get_float_as_percentage,
    get_float_as_string,
    get_gender_as_string,
    get_list_as_string,
    get_path_as_string,
    get_prep_category_as_string,
    get_report_string,
)


def test_get_report_string():
    """Test formatting an empty value."""

    # GIVEN a not valid empty field
    none_field: Any = None

    # WHEN performing the validation
    output: str = get_report_string(none_field)

    # THEN check if the input value was formatted correctly
    assert output == NA_FIELD


def test_get_boolean_as_string():
    """Test boolean formatting for the delivery report."""

    # GIVEN a not formatted inputs
    none_field: Any = None
    true_field: bool = True
    false_field: bool = False
    not_bool_field: str = "not a boolean"

    # WHEN performing the validation
    validated_none_field: str = get_boolean_as_string(none_field)
    validated_true_field: str = get_boolean_as_string(true_field)
    validated_false_field: str = get_boolean_as_string(false_field)
    validated_not_bool_field = get_boolean_as_string(not_bool_field)

    # THEN check if the input values were formatted correctly
    assert validated_none_field == NA_FIELD
    assert validated_true_field == YES_FIELD
    assert validated_false_field == NO_FIELD
    assert validated_not_bool_field == NA_FIELD


def test_get_float_as_string():
    """Test the validation of a float value."""

    # GIVEN a valid float input
    float_value: float = 12.3456789

    # WHEN performing the validation
    validated_float_value: str = get_float_as_string(float_value)

    # THEN check if the input value was formatted correctly
    assert validated_float_value == "12.35"


def test_get_float_as_string_zero_input():
    """Tests the validation of a float value when input is zero."""

    # GIVEN a valid float input
    float_value: float = 0.0

    # WHEN performing the validation
    validated_float_value: str = get_float_as_string(float_value)

    # THEN check if the input value was formatted correctly
    assert validated_float_value == "0.0"


def test_get_float_as_percentage():
    """Test the validation of a percentage value."""

    # GIVEN a not formatted percentage
    pct_value: float = 0.9876

    # WHEN performing the validation
    validated_pct_value: str = get_float_as_percentage(pct_value)

    # THEN check if the input value was formatted correctly
    assert validated_pct_value == "98.76"


def test_get_float_as_percentage_zero_input():
    """Test the validation of a percentage value when input is zero."""

    # GIVEN a zero input
    pct_value: float = 0.0

    # WHEN performing the validation
    validated_pct_value: str = get_float_as_percentage(pct_value)

    # THEN check if the input value was formatted correctly
    assert validated_pct_value == "0.0"


def test_get_date_as_string(timestamp_now: datetime):
    """Test the validation of a datetime object."""

    # GIVEN a datetime object

    # WHEN performing the validation
    validated_date_value: str = get_date_as_string(timestamp_now)

    # THEN check if the input values were formatted correctly
    assert validated_date_value == timestamp_now.date().__str__()


def test_get_list_as_string():
    """Test if a list is transformed into a string of comma separated values."""

    # GIVEN a mock list
    mock_list: list[str] = ["I am", "a", "list"]

    # WHEN performing the validation
    validated_list: str = get_list_as_string(mock_list)

    # THEN check if the input values were formatted correctly
    assert validated_list == "I am, a, list"


def test_get_path_as_string(filled_file: Path):
    """Test file path name extraction."""

    # GIVEN a mock path

    # WHEN performing the validation
    path_name: str = get_path_as_string(filled_file)

    # THEN check if the input values were formatted correctly
    assert path_name == "a_file.txt"


def test_get_gender_as_string():
    """Test report gender parsing."""

    # GIVEN an invalid gender category
    gender: Gender = Gender.FEMALE
    invalid_gender: str = "not_a_gender"

    # WHEN performing the validation
    validated_gender: str = get_gender_as_string(gender)
    validated_invalid_gender: str = get_gender_as_string(invalid_gender)

    # THEN check if the gender has been correctly formatted
    assert validated_gender == REPORT_GENDER.get("female")
    assert validated_invalid_gender == NA_FIELD


def test_get_prep_category_as_string(caplog: LogCaptureFixture):
    """Test validation on a preparation category."""

    # GIVEN an invalid prep category
    prep_category: OrderType = OrderType.RML

    # WHEN performing the validation

    # THEN check if an exception was raised
    with pytest.raises(ValueError):
        get_prep_category_as_string(prep_category)
    assert "The delivery report generation does not support RML samples" in caplog.text


def test_get_analysis_type_as_string():
    """Test analysis type formatting for the delivery report generation."""

    # GIVEN a WGS analysis type and a model info dictionary
    analysis_type: AnalysisType = AnalysisType.WHOLE_GENOME_SEQUENCING
    model_info: ValidationInfo = ValidationInfo
    model_info.data: dict[str, Any] = {"pipeline": Pipeline.MIP_DNA.value}

    # WHEN performing the validation
    validated_analysis_type: str = get_analysis_type_as_string(
        analysis_type=analysis_type, info=model_info
    )

    # THEN check if the input value was formatted correctly
    assert validated_analysis_type == analysis_type.value


def test_get_analysis_type_as_string_balsamic():
    """Test analysis type formatting for the delivery report generation."""

    # GIVEN a WGS analysis type and a model info dictionary
    analysis_type: str = "tumor_normal_wgs"
    model_info: ValidationInfo = ValidationInfo
    model_info.data: dict[str, Any] = {"pipeline": Pipeline.BALSAMIC.value}

    # WHEN performing the validation
    validated_analysis_type: str = get_analysis_type_as_string(
        analysis_type=analysis_type, info=model_info
    )

    # THEN check if the input value was formatted correctly
    assert validated_analysis_type == "Tumör/normal (helgenomsekvensering)"
