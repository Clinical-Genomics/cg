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
        try:
            metadata_for_samples: dict[str, SampleMetadata] = {}

            for sample in case.samples:
                if is_sample_external_negative_control(sample):
                    metadata_for_external_negative_control: (
                        SampleMetadata
                    ) = self.parse_metadata_for_sample(sample=sample)
                    continue
                else:
                    metadata_for_samples[sample.internal_id] = self.parse_metadata_for_sample(
                        sample=sample
                    )

            internal_negative_control_sample: (
                Sample
            ) = self.get_internal_negative_control_sample_for_case(case=case)

            metadata_for_internal_negative_control = self.parse_metadata_for_sample(
                sample=internal_negative_control_sample
            )

            return SamplesMetadataMetrics(
                samples=metadata_for_samples,
                internal_negative_control=metadata_for_internal_negative_control,
                external_negative_control=metadata_for_external_negative_control,
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

    def get_internal_negative_control_sample_for_case(self, case: Case) -> Sample:
        try:
            internal_negative_control_id: str = get_internal_negative_control_id(
                lims=self.lims, case=case
            )

            internal_negative_control_sample: Sample = self.status_db.get_sample_by_internal_id(
                internal_id=internal_negative_control_id
            )

            return internal_negative_control_sample
        except Exception as exception_object:
            raise CgError() from exception_object
