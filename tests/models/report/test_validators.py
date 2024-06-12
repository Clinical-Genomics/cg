"""Tests delivery report models validators."""

from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from _pytest.logging import LogCaptureFixture
from pydantic import ValidationInfo

from cg.constants import NA_FIELD, NO_FIELD, REPORT_SEX, YES_FIELD, Workflow
from cg.constants.constants import AnalysisType
from cg.constants.subject import Sex
from cg.models.delivery.delivery import DeliveryFile
from cg.models.orders.constants import OrderType
from cg.models.report.validators import (
    get_analysis_type_as_string,
    get_boolean_as_string,
    get_date_as_string,
    get_delivered_files_as_file_names,
    get_float_as_percentage,
    get_list_as_string,
    get_number_as_string,
    get_path_as_string,
    get_prep_category_as_string,
    get_report_string,
    get_sex_as_string,
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


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        (12.3456789, "12.35"),  # Test for a valid float input
        (0.0, "0.0"),  # Test for float zero input
        (5, "5.0"),  # Test for a valid integer input
        (0, "0.0"),  # Test for integer zero input
        (None, NA_FIELD),  # Test for None input
        ("1.2", "1.2"),  # Test for valid string input
        ("invalid", ValueError),  # Test for an invalid string input
    ],
)
def test_get_number_as_string(input_value: Any, expected_output: str, caplog: LogCaptureFixture):
    """Test the validation and formatting of numbers."""

    # GIVEN a list of number inputs and their expected values

    if expected_output == ValueError:
        # WHEN getting a string representation of a number
        with pytest.raises(ValueError):
            get_number_as_string(input_value)

        # THEN a ValueError should have been raised for an invalid number input
        assert f"Value {input_value} cannot be converted to float" in caplog.text
    else:
        # WHEN getting a string representation of a number
        validated_float_value = get_number_as_string(input_value)

        # THEN the expected output should be correctly formatted
        assert validated_float_value == expected_output


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


def test_get_list_paths_as_strings(filled_file: Path):
    """Test file path name extraction from a list."""

    # GIVEN a list of delivery files
    path_list: list[DeliveryFile] = [
        DeliveryFile(source_path=filled_file, destination_path=filled_file)
    ]

    # WHEN validating the provided list of delivery paths
    path_name_list: list[str] = get_delivered_files_as_file_names(path_list)

    # THEN the returned list should contain the file names
    assert path_name_list.pop() == "a_file.txt"


def test_get_path_as_string(filled_file: Path):
    """Test file path name extraction."""

    # GIVEN a mock path

    # WHEN performing the validation
    path_name: str = get_path_as_string(filled_file)

    # THEN check if the input values were formatted correctly
    assert path_name == "a_file.txt"


def test_get_sex_as_string():
    """Test report sex parsing."""

    # GIVEN an invalid sex category
    sex = Sex.FEMALE
    invalid_sex = "not_a_sex"

    # WHEN performing the validation
    validated_sex: str = get_sex_as_string(sex)
    validated_invalid_sex: str = get_sex_as_string(invalid_sex)

    # THEN check if the sex has been correctly formatted
    assert validated_sex == REPORT_SEX.get(sex)
    assert validated_invalid_sex == NA_FIELD


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
    model_info.data: dict[str, Any] = {"workflow": Workflow.MIP_DNA.value}

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
    model_info.data: dict[str, Any] = {"workflow": Workflow.BALSAMIC.value}

    # WHEN performing the validation
    validated_analysis_type: str = get_analysis_type_as_string(
        analysis_type=analysis_type, info=model_info
    )

    # THEN check if the input value was formatted correctly
    assert validated_analysis_type == "Tumör/normal (helgenomsekvensering)"
