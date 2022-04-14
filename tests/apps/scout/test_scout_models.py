"""Tests for the Scout serialisation models"""

import json

from cg.apps.scout.scout_export import ScoutExportCase, DiagnosisPhenotypes
from cg.constants.subject import Gender, PlinkGender, RelationshipStatus
from cg.constants.pedigree import Pedigree


def test_validate_case_father_none(none_case_output: str):
    """Test to validate a case when there are mandatory fields with the value None"""
    cases = json.loads(none_case_output)
    case = cases[0]
    # GIVEN a case that has parent set to None
    assert case["individuals"][0][Pedigree.FATHER] is None

    # WHEN validating the output with model
    case_obj = ScoutExportCase(**case)

    case_dict = case_obj.dict()

    # THEN assert father is set to string 0
    assert case_dict["individuals"][0][Pedigree.FATHER] == RelationshipStatus.HAS_NO_PARENT

    # THEN assert that '_id' has been changed to 'id'
    assert "_id" not in case_dict
    assert "id" in case_dict


def test_validate_case_parents_none(none_case_output: str):
    """Test to validate a case when there are mandatory fields with the value None"""
    cases = json.loads(none_case_output)
    case = cases[0]

    # GIVEN a case that has parent set to None
    assert case["individuals"][0][Pedigree.FATHER] is None
    assert case["individuals"][0][Pedigree.MOTHER] is None

    # WHEN validating the output with model
    case_obj = ScoutExportCase(**case)

    # THEN assert father and mother is set to string 0
    assert case_obj.dict()["individuals"][0][Pedigree.FATHER] == RelationshipStatus.HAS_NO_PARENT
    assert case_obj.dict()["individuals"][0][Pedigree.MOTHER] == RelationshipStatus.HAS_NO_PARENT


def test_get_diagnosis_phenotypes(export_cases_output: str, omim_disease_nr: int):
    """Test getting diagnosis phenotypes from cases export"""
    cases = json.loads(export_cases_output)
    case = cases[0]

    # Given a case with a diagnosis_phenotype
    assert case["diagnosis_phenotypes"][0]["disease_nr"] == omim_disease_nr

    # WHEN validating the output with model
    case_obj = ScoutExportCase(**case)

    # THEN assert that it was successfully created
    assert isinstance(case_obj.diagnosis_phenotypes[0], DiagnosisPhenotypes)

    # THEN assert that the disease nr is set
    assert case_obj.diagnosis_phenotypes[0].disease_nr == omim_disease_nr


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
    assert case["individuals"][0][Pedigree.SEX] == Gender.OTHER

    # WHEN validating the output with model
    case_obj = ScoutExportCase(**case)

    # THEN assert that the sex has been converted to "0"
    assert case_obj.dict()["individuals"][0][Pedigree.SEX] == PlinkGender.UNKNOWN
