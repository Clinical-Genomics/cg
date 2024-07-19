from cg.apps.lims.api import LimsAPI
from cg.exc import CgError
from cg.meta.workflow.mutant.metadata_parser.models import SampleMetadata, SamplesMetadataMetrics
from cg.meta.workflow.mutant.metadata_parser.utils import (
    get_internal_negative_control_id,
    is_sample_external_negative_control,
)
from cg.models.cg_config import LOG
from cg.store.store import Store
from cg.store.models import Case, Sample


class MetadataParser:
    def __init__(self, status_db: Store, lims: LimsAPI) -> None:
        self.status_db = status_db
        self.lims = lims

    def parse_metadata(self, case: Case) -> SamplesMetadataMetrics:
        metadata_for_case = self.parse_metadata_for_case(case=case)
        try:
            metadata_for_internal_negative_control = self.parse_metadata_for_internal_negative_control(
                metadata_for_case=metadata_for_case
            )
        except Exception as exception_object:
            raise CgError from exception_object
        if not metadata_for_internal_negative_control:
            LOG.error(f"Could not find an internal negative control for {case.internal_id}")
            
        metadata = metadata_for_case | metadata_for_internal_negative_control
        return SamplesMetadataMetrics(samples=metadata)

    def parse_metadata_for_case(self, case: Case) -> dict[str, SampleMetadata]:
        metadata_for_case: dict[str, SampleMetadata] = {}

        for sample in case.samples:
            is_external_negative_control: bool = is_sample_external_negative_control(sample)

            sample_metadata = SampleMetadata(
                sample_internal_id=sample.internal_id,
                sample_name=sample.name,
                is_external_negative_control=is_external_negative_control,
                reads=sample.reads,
                target_reads=sample.application_version.application.target_reads,
                percent_reads_guaranteed=sample.application_version.application.percent_reads_guaranteed,
            )

            metadata_for_case[sample.internal_id] = sample_metadata

        return metadata_for_case

    def parse_metadata_for_internal_negative_control(
        self, metadata_for_case: SamplesMetadataMetrics
    ) -> dict[str, SampleMetadata] | None:
        try:
            internal_negative_control_id: Sample = get_internal_negative_control_id(
                self.lims, metadata_for_case
            )

            internal_negative_control: Sample = self.status_db.get_sample_by_internal_id(
                internal_negative_control_id
            )
            internal_negative_control_metadata = SampleMetadata(
                sample_internal_id=internal_negative_control.internal_id,
                sample_name=internal_negative_control.name,
                is_external_negative_control=False,
                is_internal_negative_control=True,
                reads=internal_negative_control.reads,
                target_reads=internal_negative_control.application_version.application.target_reads,
                percent_reads_guaranteed=internal_negative_control.application_version.application.percent_reads_guaranteed,
            )

            return {internal_negative_control.internal_id: internal_negative_control_metadata}
        except Exception as exception_object:
            raise CgError from exception_object

