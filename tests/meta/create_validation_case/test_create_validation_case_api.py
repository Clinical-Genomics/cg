"""Module to test the CreateValidationCaseAPI."""

from cg.meta.create_validation_cases.validation_case_data import ValidationCaseData
from cg.meta.create_validation_cases.validation_cases_api import CreateValidationCaseAPI


def test_create_validation_case(
    create_validation_api: CreateValidationCaseAPI,
    case_id_with_multiple_samples: str,
    validation_sample_id: str,
    validation_case_id: str,
):

    # GIVEN a CreateValidationCaseAPI

    # WHEN creating a validation case
    create_validation_api.create_validation_case(
        case_id=case_id_with_multiple_samples, case_name=case_id_with_multiple_samples
    )

    # THEN a validation case is created in statusDB
    assert create_validation_api.status_db.get_case_by_internal_id(validation_case_id)
    # THEN validation samples are created in statusDB
    assert create_validation_api.status_db.get_sample_by_internal_id(validation_sample_id)

    # THEN validation sample bundles are created in Housekeeper

    # THEN validation sample fastq files are created in Housekeeper
