"""Tests for the Scout serialisation models"""
from cg.apps.scout.scout_export import DiagnosisPhenotypes, ScoutExportCase
from cg.apps.scout.validators import set_gender_if_other, set_parent_if_missing
from cg.constants.constants import FileFormat
from cg.constants.gene_panel import GENOME_BUILD_37
from cg.constants.pedigree import Pedigree
from cg.constants.subject import Gender, PlinkGender, RelationshipStatus
from cg.io.controller import ReadStream


def test_validate_case_father_none(none_case_raw: dict):
    """Test to validate a case when there are mandatory fields with the value None"""

    # GIVEN a case that has parent set to None
    assert none_case_raw["individuals"][0][Pedigree.FATHER] is None

    # WHEN validating the output with model
    case_obj = ScoutExportCase.model_validate(none_case_raw)

    case_dict = case_obj.model_dump()

    # THEN assert father is set to string 0
    assert case_dict["individuals"][0][Pedigree.FATHER] == str(
        RelationshipStatus.HAS_NO_PARENT.value
    )

    # THEN assert that '_id' has been changed to 'id'
    assert "_id" not in case_dict
    assert "id" in case_dict


def test_validate_case_father_int(none_case_raw: dict):
    """Test to validate string coercion when the father is set to 0."""

    # GIVEN a case that has parent set to 0
    none_case_raw["individuals"][0][Pedigree.FATHER] = 0

    # WHEN validating the output with model
    case_obj = ScoutExportCase.model_validate(none_case_raw)

    case_dict = case_obj.model_dump()

    # THEN assert father is set to string 0
    assert case_dict["individuals"][0][Pedigree.FATHER] == str(
        RelationshipStatus.HAS_NO_PARENT.value
    )

    # THEN assert that '_id' has been changed to 'id'
    assert "_id" not in case_dict
    assert "id" in case_dict


def test_validate_case_parents_none(none_case_raw: dict):
    """Test to validate a case when there are mandatory fields with the value None"""

    # GIVEN a case that has parent set to None
    assert none_case_raw["individuals"][0][Pedigree.FATHER] is None
    assert none_case_raw["individuals"][0][Pedigree.MOTHER] is None

    # WHEN validating the output with model
    case_obj = ScoutExportCase.model_validate(none_case_raw)

    # THEN assert father and mother is set to string 0
    assert case_obj.model_dump()["individuals"][0][Pedigree.FATHER] == str(
        RelationshipStatus.HAS_NO_PARENT.value
    )
    assert case_obj.model_dump()["individuals"][0][Pedigree.MOTHER] == str(
        RelationshipStatus.HAS_NO_PARENT.value
    )


def test_get_diagnosis_phenotypes(export_cases_output: str, omim_disease_nr: int):
    """Test getting diagnosis phenotypes from cases export"""
    cases: list = ReadStream.get_content_from_stream(
        file_format=FileFormat.JSON, stream=export_cases_output
    )
    case = cases[0]

    # Given a case with a diagnosis_phenotype
    assert case["diagnosis_phenotypes"][0]["disease_nr"] == omim_disease_nr

    # WHEN validating the output with model
    case_obj = ScoutExportCase.model_validate(case)

    # THEN assert that it was successfully created
    assert isinstance(case_obj.diagnosis_phenotypes[0], DiagnosisPhenotypes)

    # THEN assert that the disease nr is set
    assert case_obj.diagnosis_phenotypes[0].disease_nr == omim_disease_nr


def test_validate_empty_diagnosis_phenotypes(none_case_raw: dict):
    """Test to validate a case when the diagnosis phenotypes is an empty list"""

    # GIVEN a case that has parent set to None
    assert none_case_raw["diagnosis_phenotypes"] == []

    # WHEN validating the output with model
    case_obj = ScoutExportCase.model_validate(none_case_raw)

    # THEN assert diagnosis phenotypes is set to None
    assert case_obj.model_dump()["diagnosis_phenotypes"] == []


def test_convert_other_sex(other_sex_case_output: str):
    """Test to validate a case when the is set to 'other'"""
    cases: list = ReadStream.get_content_from_stream(
        file_format=FileFormat.JSON, stream=other_sex_case_output
    )
    case = cases[0]
    # GIVEN a case that has parent set to None
    assert case["individuals"][0][Pedigree.SEX] == Gender.OTHER

    # WHEN validating the output with model
    case_obj = ScoutExportCase.model_validate(case)

    # THEN assert that the sex has been converted to "0"
    assert case_obj.model_dump()["individuals"][0][Pedigree.SEX] == PlinkGender.UNKNOWN


def test_validate_rank_score_model_float(other_sex_case_output: str):
    """Test to validate a case when the is set to 'other'."""
    cases: list = ReadStream.get_content_from_stream(
        file_format=FileFormat.JSON, stream=other_sex_case_output
    )
    case = cases[0]

    # GIVEN a case that has a float value as rank_model_version
    case["rank_model_version"] = 1.2

    # WHEN validating the output with model
    case_obj = ScoutExportCase.model_validate(case)

    # THEN assert that the rank_model_version is a string
    assert case_obj.rank_model_version == "1.2"


def test_validate_missing_genome_build(other_sex_case_output: str):
    """Test to validate a case when the is set to 'other'"""
    cases: list = ReadStream.get_content_from_stream(
        file_format=FileFormat.JSON, stream=other_sex_case_output
    )
    case = cases[0]
    # GIVEN a case that has a float value as rank_model_version
    case["genome_build"] = None

    # WHEN validating the output with model
    case_obj = ScoutExportCase.model_validate(case)

    # THEN assert that the rank_model_version is a string
    assert case_obj.genome_build == GENOME_BUILD_37


def test_set_parent_when_provided():
    """Test to validate that the parent value is not altered if a string is provided."""

    # GIVEN a valid parent
    father: str = Pedigree.FATHER

    # WHEN running "set_parent_if_missing"
    validated_father: str = set_parent_if_missing(father)

    # THEN the returned string should not have been altered
    assert validated_father == father


def test_set_parent_when_not_provided():
    """Test to validate that the parent value is altered if a string is not provided."""

    # GIVEN that no parent is provided
    parent = None

    # WHEN running "set_parent_if_missing"
    validated_parent: str = set_parent_if_missing(parent=parent)

    # THEN the returned string should have been set to RelationshipStatus.HAS_NO_PARENT
    assert validated_parent == str(RelationshipStatus.HAS_NO_PARENT.value)


def test_set_gender_if_provided():
    """Test to validate that the gender is not altered when set and not Gender.OTHER."""

    # GIVEN a gender which is not Gender.OTHER as input
    gender: PlinkGender = PlinkGender.FEMALE

    # WHEN running "set_gender_if_other"
    validated_gender: str = set_gender_if_other(gender)

    # THEN the returned string should not have been altered
    assert validated_gender == gender


def test_set_gender_if_other():
    """Test to validate that the gender is altered when set to Gender.OTHER."""

    # GIVEN Gender.OTHER as input
    gender: Gender = Gender.OTHER

    # WHEN running "set_gender_if_other"
    validated_gender: str = set_gender_if_other(gender)

    # THEN the returned gender should be PlinkGender.UNKNOWN
    assert validated_gender == PlinkGender.UNKNOWN
