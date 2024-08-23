"""Tests delivery report models validators."""

from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from _pytest.logging import LogCaptureFixture
from pydantic_core.core_schema import ValidationInfo
from pytest_mock import MockFixture

from cg.apps.lims import LimsAPI
from cg.constants import (
    NA_FIELD,
    YES_FIELD,
    NO_FIELD,
    REPORT_SEX,
    Sex,
    RIN_MAX_THRESHOLD,
    RIN_MIN_THRESHOLD,
)
from cg.constants.constants import AnalysisType, Workflow
from cg.meta.delivery_report.delivery_report_api import DeliveryReportAPI
from cg.meta.delivery_report.rnafusion import RnafusionDeliveryReportAPI
from cg.models.analysis import NextflowAnalysis
from cg.models.delivery.delivery import DeliveryFile
from cg.models.delivery_report.metadata import RnafusionSampleMetadataModel
from cg.models.delivery_report.validators import (
    get_report_string,
    get_boolean_as_string,
    get_number_as_string,
    get_float_as_percentage,
    get_date_as_string,
    get_list_as_string,
    get_delivered_files_as_file_names,
    get_path_as_string,
    get_sex_as_string,
    get_prep_category_as_string,
    get_analysis_type_as_string,
)
from cg.models.orders.constants import OrderType
from cg.store.models import Case, Analysis, Sample


def test_get_report_string():
    """Test formatting an empty value."""

    # GIVEN a not valid empty field
    none_field = None

    # WHEN performing the validation
    output: str = get_report_string(none_field)

    # THEN check if the input value was formatted correctly
    assert output == NA_FIELD


def test_get_boolean_as_string():
    """Test boolean formatting for the delivery report."""

    # GIVEN a not formatted inputs
    none_field = None
    true_field = True
    false_field = False
    not_a_bool_field = "not a boolean"

    # WHEN performing the validation
    validated_none_field: str = get_boolean_as_string(none_field)
    validated_true_field: str = get_boolean_as_string(true_field)
    validated_false_field: str = get_boolean_as_string(false_field)
    validated_not_bool_field = get_boolean_as_string(not_a_bool_field)

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
        validated_float_value: str = get_number_as_string(input_value)

        # THEN the expected output should be correctly formatted
        assert validated_float_value == expected_output


def test_get_float_as_percentage():
    """Test the validation of a percentage value."""

    # GIVEN a not formatted percentage
    pct_value = 0.9876

    # WHEN performing the validation
    validated_pct_value: str = get_float_as_percentage(pct_value)

    # THEN check if the input value was formatted correctly
    assert validated_pct_value == "98.76"


def test_get_float_as_percentage_zero_input():
    """Test the validation of a percentage value when input is zero."""

    # GIVEN a zero input
    pct_value = 0.0

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
    assert validated_date_value == str(timestamp_now.date())


def test_get_list_as_string():
    """Test if a list is transformed into a string of comma separated values."""

    # GIVEN a mocked list
    mocked_list = ["I am", "a", "list"]

    # WHEN performing the validation
    validated_list: str = get_list_as_string(mocked_list)

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
    assert path_name_list[0] == "a_file.txt"


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
    analysis_type: str = AnalysisType.WHOLE_GENOME_SEQUENCING
    model_info = ValidationInfo
    model_info.data = {"workflow": Workflow.MIP_DNA.value}

    # WHEN performing the validation
    validated_analysis_type: str = get_analysis_type_as_string(
        analysis_type=analysis_type, info=model_info
    )

    # THEN check if the input value was formatted correctly
    assert validated_analysis_type == analysis_type.value


def test_get_analysis_type_as_string_balsamic():
    """Test analysis type formatting for the delivery report generation."""

    # GIVEN a WGS analysis type and a model info dictionary
    analysis_type = "tumor_normal_wgs"
    model_info = ValidationInfo
    model_info.data = {"workflow": Workflow.BALSAMIC.value}

    # WHEN performing the validation
    validated_analysis_type: str = get_analysis_type_as_string(
        analysis_type=analysis_type, info=model_info
    )

    # THEN check if the input value was formatted correctly
    assert validated_analysis_type == "Tumör/normal (helgenomsekvensering)"


def test_check_supported_workflow_mismatch_between_ordered_and_started(
    raredisease_delivery_report_api: DeliveryReportAPI,
    raredisease_case_id: str,
    caplog: LogCaptureFixture,
):
    """Test validation error if a customer requested workflow does not match the data analysis."""

    # GIVEN a delivery report API

    # GIVEN a case object that has been ordered with Raredisease workflow
    case: Case = raredisease_delivery_report_api.analysis_api.status_db.get_case_by_internal_id(
        raredisease_case_id
    )

    # GIVEN an analysis that has been started with the Rnafusion workflow
    analysis: Analysis = case.analyses[0]
    analysis.workflow = Workflow.RNAFUSION

    # WHEN retrieving case analysis data

    # THEN a validation error should be raised
    with pytest.raises(ValueError):
        raredisease_delivery_report_api.get_case_analysis_data(case=case, analysis=analysis)
    assert (
        f"The analysis requested by the customer ({case.data_analysis}) does not match the one executed "
        f"({analysis.workflow})" in caplog.text
    )


def test_check_supported_workflow_not_delivery_report_supported(
    raredisease_delivery_report_api: DeliveryReportAPI,
    raredisease_case_id: str,
    caplog: LogCaptureFixture,
):
    """Test validation error if a customer requested workflow does not match the data analysis."""

    # GIVEN a delivery report API

    # GIVEN a FLUFFY case object
    case: Case = raredisease_delivery_report_api.analysis_api.status_db.get_case_by_internal_id(
        raredisease_case_id
    )
    case.data_analysis = Workflow.FLUFFY

    # GIVEN an analysis that has been started with the FLUFFY workflow
    analysis: Analysis = case.analyses[0]
    analysis.workflow = Workflow.FLUFFY

    # WHEN retrieving case analysis data

    # THEN a validation error should be raised
    with pytest.raises(ValueError):
        raredisease_delivery_report_api.get_case_analysis_data(case=case, analysis=analysis)
    assert (
        f"The workflow {case.data_analysis} does not support delivery report generation"
        in caplog.text
    )


@pytest.mark.parametrize(
    "input_rin, expected_rin",
    [
        (RIN_MAX_THRESHOLD, str(float(RIN_MAX_THRESHOLD))),  # Test for a valid integer input
        (RIN_MAX_THRESHOLD + 1, NA_FIELD),  # Test for an integer above the allowed threshold
        (RIN_MIN_THRESHOLD - 1, NA_FIELD),  # Test for an integer below the allowed threshold
        (None, NA_FIELD),  # Test for a None input
    ],
)
def test_ensure_rin_thresholds(
    rnafusion_case_id: str,
    sample_id: str,
    input_rin: int | float,
    expected_rin: str,
    rnafusion_delivery_report_api: RnafusionDeliveryReportAPI,
    rnafusion_mock_analysis_finish: None,
    mocker: MockFixture,
):
    """Test Rnafusion RIN value validation."""

    # GIVEN a Rnafusion case and associated sample
    case: Case = rnafusion_delivery_report_api.status_db.get_case_by_internal_id(
        internal_id=rnafusion_case_id
    )
    sample: Sample = rnafusion_delivery_report_api.status_db.get_sample_by_internal_id(
        internal_id=sample_id
    )

    # GIVEN an analysis metadata object
    analysis_metadata: NextflowAnalysis = (
        rnafusion_delivery_report_api.analysis_api.get_latest_metadata(rnafusion_case_id)
    )

    # GIVEN a specific RIN value
    mocker.patch.object(LimsAPI, "get_sample_rin", return_value=input_rin)

    # WHEN getting the sample metadata
    sample_metadata: RnafusionSampleMetadataModel = (
        rnafusion_delivery_report_api.get_sample_metadata(
            case=case, sample=sample, analysis_metadata=analysis_metadata
        )
    )

    # THEN the sample RIN value should match the expected RIN value
    assert sample_metadata.rin == expected_rin
