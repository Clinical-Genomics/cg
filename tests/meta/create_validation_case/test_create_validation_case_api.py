"""Module to test the CreateValidationCaseAPI."""

from pathlib import Path

from housekeeper.store.models import File

from cg.constants import SequencingFileTag
from cg.meta.create_validation_cases.validation_case_data import ValidationCaseData
from cg.meta.create_validation_cases.validation_cases_api import CreateValidationCaseAPI


def test_get_new_fastq_file_path(validation_case_data: ValidationCaseData, fixtures_dir: Path):
    # GIVEN a file path and a new file name
    fastq_file = Path(fixtures_dir, validation_case_data.validation_samples[0].from_sample)
    expected_new_file_name = Path(
        fixtures_dir, validation_case_data.validation_samples[0].internal_id
    )

    # WHEN getting the new fastq file path
    new_file_path = CreateValidationCaseAPI.get_new_fastq_file_path(
        fastq_file=fastq_file,
        validation_sample=validation_case_data.validation_samples[0],
    )

    # THEN the new file path is correct
    assert new_file_path == expected_new_file_name


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
