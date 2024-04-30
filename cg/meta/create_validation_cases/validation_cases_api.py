"""Module that holds the api to create validation cases."""

import logging
import os
from pathlib import Path

from housekeeper.store.models import File, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.housekeeper_tags import VALIDATION_TAG
from cg.meta.create_validation_cases.validation_case_data import ValidationCaseData
from cg.meta.create_validation_cases.validation_data_input import ValidationDataInput
from cg.store.models import Case, CaseSample, Sample
from cg.store.store import Store
from cg.utils.files import copy_file, get_files_matching_pattern, rename_file

LOG = logging.getLogger(__name__)


class CreateValidationCaseAPI:

    def __init__(self, status_db: Store, housekeeper_api: HousekeeperAPI, dry_run: bool = False):
        self.status_db: Store = status_db
        self.hk_api: HousekeeperAPI = housekeeper_api
        self.dry_run = dry_run

    def get_validation_case_data(self, validation_data_input: ValidationDataInput):
        return ValidationCaseData(
            status_db=self.status_db,
            validation_data_input=validation_data_input,
        )

    def store_validation_samples(self, validation_case_data: ValidationCaseData) -> None:
        """
        Add a validation sample entry to StatusDB.
        Raises:
            ValueError
        """
        for sample in validation_case_data.validation_samples:
            if self.status_db.sample_with_id_exists(sample_id=sample.internal_id):
                raise ValueError(f"Sample {sample.internal_id} already exists in StatusDB.")
            LOG.info(
                f"New validation sample created: {sample.internal_id} from {sample.from_sample}"
                f"Application tag set to: {sample.application_version.application.tag}"
            )
            if not self.dry_run:
                self.status_db.session.add(sample)
                LOG.info(f"Added {sample.name} to StatusDB.")

    def store_validation_case(self, validation_case_data: ValidationCaseData) -> None:
        """
        Add a validation case entry to StatusDB.
        """
        validation_case: Case = validation_case_data.validation_case
        if self.status_db.case_with_name_exists(case_name=validation_case.name):
            LOG.info(f"Case with name {validation_case.name} already exists in StatusDB.")
            return
        if not self.dry_run:
            self.status_db.session.add(validation_case)
            LOG.info(f"New validation case created: {validation_case.internal_id}")

    def _link_sample_to_case(self, validation_case_data: ValidationCaseData) -> None:
        """Create a link between sample and case in statusDB."""
        for sample in validation_case_data.validation_samples:
            sample_case_link: CaseSample = self.status_db.relate_sample(
                case=validation_case_data.validation_case,
                sample=sample,
                status=self._get_sample_status(sample),
            )
            if self.dry_run:
                return
            self.status_db.session.add(sample_case_link)
            LOG.info(
                f"Related sample {sample.internal_id} to {validation_case_data.validation_case.internal_id}"
            )

    @staticmethod
    def _get_sample_status(sample: Sample) -> str:
        """Return the status of a sample."""
        return sample.links[0].status if sample.links else "unknown"

    def create_validation_case_in_statusdb(self, validation_case_data: ValidationCaseData) -> None:
        """
        Add the validation samples and case to statusDB and generate the sample case link.
        """
        try:
            self.store_validation_samples(validation_case_data)
            self.store_validation_case(validation_case_data)
            self._link_sample_to_case(validation_case_data)
            self.status_db.session.commit()
        except Exception as error:
            LOG.warning(f"An error occurred {repr(error)}")
            self.status_db.session.rollback()

    def create_validation_sample_bundles(self, validation_samples: list[Sample]) -> None:
        for validation_sample in validation_samples:
            self.hk_api.create_new_bundle_and_version(validation_sample.internal_id)

    def copy_original_sample_bundle_files(self, validation_samples: list[Sample]) -> None:
        """Copy the fastq files from the original sample bundle into the new validation sample bundle"""
        for validation_sample in validation_samples:
            fastq_files: list[File] = self.hk_api.get_files_from_latest_version(
                bundle_name=validation_sample.from_sample, tags=[SequencingFileTag.FASTQ]
            )
            validation_bundle_path: Path = self.hk_api.get_latest_bundle_version(
                bundle_name=validation_sample.internal_id
            ).full_path
            if not validation_bundle_path.exists():
                os.makedirs(validation_bundle_path)
            for fastq_file in fastq_files:
                copy_file(file_path=Path(fastq_file.full_path), destination=validation_bundle_path)

    def rename_and_add_original_sample_bundle_files(self, validation_samples: list[Sample]) -> None:
        """Rename the fastq files to use the new validation sample internal id."""
        for validation_sample in validation_samples:
            validation_bundle_path: Path = self.hk_api.get_latest_bundle_version(
                bundle_name=validation_sample.internal_id
            ).full_path
            fastq_files: list[Path] = get_files_matching_pattern(
                directory=validation_bundle_path, pattern="*." + SequencingFileTag.FASTQ + ".*"
            )
            for fastq_file in fastq_files:
                new_fast_file_path = self.get_new_fastq_file_path(
                    fastq_file=fastq_file, validation_sample=validation_sample
                )
                rename_file(file_path=fastq_file, renamed_file_path=new_fast_file_path)
                new_tags: list[str] = self.get_new_tags(validation_sample)
                self.hk_api.add_and_include_file_to_latest_version(
                    bundle_name=validation_sample.internal_id,
                    file=new_fast_file_path,
                    tags=new_tags,
                )

    def get_new_tags(self, validation_sample: Sample) -> list[str]:
        """
        Get the fastq file tags from the original sample and
        replace the bundle name with the validation sample internal id.
        """
        hk_files: list[File] = self.hk_api.get_files_from_latest_version(
            bundle_name=validation_sample.from_sample, tags=[SequencingFileTag.FASTQ]
        )
        original_tags: list[str] = self.hk_api.get_tag_names_from_file(hk_files[0])
        new_tags: list[str] = [validation_sample.internal_id, VALIDATION_TAG]
        for tag in original_tags:
            if tag != validation_sample.from_sample:
                new_tags.append(tag)
        return new_tags

    @staticmethod
    def get_new_fastq_file_path(fastq_file: Path, validation_sample: Sample) -> Path:
        return Path(
            fastq_file.as_posix().replace(
                validation_sample.from_sample,
                validation_sample.internal_id,
            )
        )

    def create_validation_samples_in_housekeeper(self, validation_case_data: ValidationCaseData):
        self.create_validation_sample_bundles(validation_case_data.validation_samples)
        self.copy_original_sample_bundle_files(validation_case_data.validation_samples)
        self.rename_and_add_original_sample_bundle_files(validation_case_data.validation_samples)

    def create_validation_case(
        self,
        case_id: str,
        case_name: str,
        data_analysis: str | None = None,
        delivery: str | None = None,
        dry_run: bool | None = False,
    ) -> None:
        """Create the validation case in statusdb and associated sample bundles in housekeeper."""
        validation_data_input = ValidationDataInput(
            case_id=case_id, case_name=case_name, data_analysis=data_analysis, delivery=delivery
        )
        validation_case_data: ValidationCaseData = self.get_validation_case_data(
            validation_data_input
        )
        if dry_run:
            LOG.info(
                f"Would have created validation case {validation_case_data.validation_case.name}"
            )
            return
        self.create_validation_case_in_statusdb(validation_case_data)
        self.create_validation_samples_in_housekeeper(validation_case_data)
