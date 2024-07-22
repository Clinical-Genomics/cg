from cg.apps.lims.api import LimsAPI
from cg.exc import CgError
from cg.meta.workflow.mutant.metadata_parser.models import SampleMetadata, SamplesMetadataMetrics
from cg.meta.workflow.mutant.metadata_parser.utils import (
    get_internal_negative_control_id,
    is_sample_external_negative_control,
)
from cg.store.store import Store
from cg.store.models import Case, Sample


class MetadataParser:
    def __init__(self, status_db: Store, lims: LimsAPI) -> None:
        self.status_db = status_db
        self.lims = lims

    def parse_metadata(self, case: Case) -> SamplesMetadataMetrics:
        metadata_for_samples: dict[str, SampleMetadata] = {}

        for sample in case.samples:
            if is_sample_external_negative_control(sample):
                metadata_for_external_negative_control: (
                    SampleMetadata
                ) = self.parse_metadata_for_external_negative_control(
                    external_negative_control_sample=sample
                )

            metadata_for_samples[sample.internal_id] = self.parse_metadata_for_sample(sample=sample)

        try:
            metadata_for_internal_negative_control: (
                SampleMetadata
            ) = self.parse_metadata_for_internal_negative_control(
                metadata_for_samples=metadata_for_samples
            )

            return SamplesMetadataMetrics(
                samples=metadata_for_samples,
                internal_control=metadata_for_internal_negative_control,
                external_control=metadata_for_external_negative_control,
            )

        except Exception as exception_object:
            raise CgError from exception_object

    def parse_metadata_for_sample(self, sample: Sample) -> SampleMetadata:
        sample_metadata = SampleMetadata(
            sample_internal_id=sample.internal_id,
            sample_name=sample.name,
            reads=sample.reads,
            target_reads=sample.application_version.application.target_reads,
            percent_reads_guaranteed=sample.application_version.application.percent_reads_guaranteed,
        )

        return sample_metadata

    def parse_metadata_for_external_negative_control(
        self, external_negative_control_sample: Sample
    ) -> SampleMetadata:
        external_negative_control_metadata = SampleMetadata(
            sample_internal_id=external_negative_control_sample.internal_id,
            sample_name=external_negative_control_sample.name,
            reads=external_negative_control_sample.reads,
            target_reads=external_negative_control_sample.application_version.application.target_reads,
            percent_reads_guaranteed=external_negative_control_sample.application_version.application.percent_reads_guaranteed,
        )
        return external_negative_control_metadata

    def parse_metadata_for_internal_negative_control(
        self, metadata_for_samples: dict[str, SampleMetadata]
    ) -> SampleMetadata:
        try:
            internal_negative_control_id: Sample = get_internal_negative_control_id(
                self.lims, metadata_for_samples
            )

            internal_negative_control: Sample = self.status_db.get_sample_by_internal_id(
                internal_negative_control_id
            )

            internal_negative_control_metadata = SampleMetadata(
                sample_internal_id=internal_negative_control.internal_id,
                sample_name=internal_negative_control.name,
                reads=internal_negative_control.reads,
                target_reads=internal_negative_control.application_version.application.target_reads,
                percent_reads_guaranteed=internal_negative_control.application_version.application.percent_reads_guaranteed,
            )

            return internal_negative_control_metadata
        except Exception as exception_object:
            raise CgError() from exception_object
