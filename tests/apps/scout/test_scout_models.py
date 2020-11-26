"""Tests for the Scout serialisation models"""

import json

from cg.apps.scout.scout_export import ScoutExportCase


def test_validate_case_father_none(none_case_output: str):
    """Test to validate a case when there are mandatory fields with the value None"""
    cases = json.loads(none_case_output)
    case = cases[0]
    # GIVEN a case that has parent set to None
    assert case["individuals"][0]["father"] is None

    # WHEN validating the output with model
    case_obj = ScoutExportCase(**case)

    # THEN assert father is set to None
    assert case_obj.dict()["individuals"][0]["father"] == "0"


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
