"""Tests for the Scout serialisation models"""

import json

from cg.apps.scout.scout_export import ScoutExportCase
from cg.constants.gender import Gender, PlinkGender


def test_validate_case_father_none(none_case_output: str):
    """Test to validate a case when there are mandatory fields with the value None"""
    cases = json.loads(none_case_output)
    case = cases[0]
    # GIVEN a case that has parent set to None
    assert case["individuals"][0]["father"] is None

    # WHEN validating the output with model
    case_obj = ScoutExportCase(**case)

    case_dict = case_obj.dict()
    # THEN assert father is set to None
    assert case_dict["individuals"][0]["father"] == "0"
    # THEN assert that '_id' has been changed to 'id'
    assert "_id" not in case_dict
    assert "id" in case_dict


def test_validate_case_parents_none(none_case_output: str):
    """Test to validate a case when there are mandatory fields with the value None"""
    cases = json.loads(none_case_output)
    case = cases[0]
    # GIVEN a case that has parent set to None
    assert case["individuals"][0]["father"] is None
    assert case["individuals"][0]["mother"] is None

    # WHEN validating the output with model
    case_obj = ScoutExportCase(**case)

    # THEN assert father is set to None
    assert case_obj.dict()["individuals"][0]["father"] == "0"
    assert case_obj.dict()["individuals"][0]["mother"] == "0"


def test_validate_empty_diagnosis_phenotypes(none_case_output: str):
    """Test to validate a case when the diagnosis phenotypes is a empty list"""
    cases = json.loads(none_case_output)
    case = cases[0]
    # GIVEN a case that has parent set to None
    assert case["diagnosis_phenotypes"] == []

    # WHEN validating the output with model
    case_obj = ScoutExportCase(**case)

    # THEN assert diagnosis phenotypes is set to None
    assert case_obj.dict()["diagnosis_phenotypes"] == []


def test_convert_other_sex(other_sex_case_output: str):
    """Test to validate a case when the is set to 'other'"""
    cases = json.loads(other_sex_case_output)
    case = cases[0]
    # GIVEN a case that has parent set to None
    assert case["individuals"][0]["sex"] == Gender.OTHER

    # WHEN validating the output with model
    case_obj = ScoutExportCase(**case)

    # THEN assert that the sex has been converted to "0"
    assert case_obj.dict()["individuals"][0]["sex"] == PlinkGender.UNKNOWN


def test_get_diagnosis_phenotypes(export_cases_output: str):
    """Test getting diagnosis phenotypes from cases export"""
    cases = json.loads(export_cases_output)
    case = cases[0]

    # Given a case with a diagnosis_phenotype
    assert case["diagnosis_phenotypes"][0]["disease_nr"] == 607208
