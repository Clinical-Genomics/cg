"""Module to test the CreateValidationCaseAPI."""

from housekeeper.store.models import File

from cg.constants import SequencingFileTag
from cg.meta.create_validation_cases.validation_cases_api import CreateValidationCaseAPI


def test_create_validation_case(
    create_validation_api: CreateValidationCaseAPI,
    case_id_with_multiple_samples: str,
    validation_sample_id: str,
    validation_case_name: str,
):

    # GIVEN a CreateValidationCaseAPI and a case id

    # WHEN creating a validation case
    create_validation_api.create_validation_case(
        case_id=case_id_with_multiple_samples, case_name=case_id_with_multiple_samples
    )

    # THEN a validation case is created in statusDB
    assert create_validation_api.status_db.get_case_by_name(validation_case_name)
    # THEN validation samples are created in statusDB
    assert create_validation_api.status_db.get_sample_by_internal_id(validation_sample_id)

    # THEN validation sample bundles are created in Housekeeper
    assert create_validation_api.hk_api.get_latest_bundle_version(validation_sample_id)

    # THEN validation sample fastq files are created in Housekeeper
    files: list[File] = create_validation_api.hk_api.get_files_from_latest_version(
        bundle_name=validation_sample_id, tags=[SequencingFileTag.FASTQ]
    )
    assert files
