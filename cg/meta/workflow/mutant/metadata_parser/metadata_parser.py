from cg.meta.workflow.mutant.metadata_parser.models import SampleMetadata, SamplesMetadata
from cg.meta.workflow.mutant.metadata_parser.utils import (
    get_internal_negative_control,
    is_sample_external_negative_control,
)
from cg.store.api.core import Store
from cg.store.models import Case


class MetadataParser:
    def __init__(self, status_db: Store) -> None:
        self.status_db = status_db

    def parse_metadata(self, case_internal_id: str) -> SamplesMetadata:
        metadata_for_case = self.parse_metadata_for_case(case_internal_id)
        metadata_for_internal_negative_control = self.parse_metadata_for_internal_negative_control()

        metadata = metadata_for_case | metadata_for_internal_negative_control

        return SamplesMetadata.model_validate(metadata)

    def parse_metadata_for_case(self, case_internal_id: str) -> dict[str, SampleMetadata]:
        case: Case = self.status_db.get_case_by_internal_id(case_internal_id)

        metadata_for_case: dict[str, SampleMetadata] = {}

        for sample in case.samples:
            is_external_negative_control: bool = is_sample_external_negative_control(sample)

            sample_metadata = SampleMetadata(
                sample_internal_id=sample.internal_id,
                sample_name=sample.name,
                is_external_negative_control=is_external_negative_control,
                reads=sample.reads,
            )

            metadata_for_case[sample.internal_id] = sample_metadata

        return metadata_for_case

    def parse_metadata_for_internal_negative_control(self) -> dict[str, SampleMetadata]:
        get_internal_negative_control()
        pass

    #         SampleMetadata(BaseModel):
    # sample_internal_id: str
    # sample_name: str
    # is_external_negative_control: bool
    # is_internal_negative_control: bool = False
    # reads: int
