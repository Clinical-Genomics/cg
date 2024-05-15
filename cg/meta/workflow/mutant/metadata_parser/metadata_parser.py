from cg.apps.lims.api import LimsAPI
from cg.constants.lims import LimsArtifactTypes, LimsProcess
from cg.meta.workflow.mutant.metadata_parser.models import SampleMetadata, SamplesMetadata
from cg.meta.workflow.mutant.metadata_parser.utils import (
    get_internal_negative_control,
    is_sample_external_negative_control,
)
from cg.models.cg_config import CGConfig
from cg.store.api.core import Store
from cg.store.models import Case, Sample


class MetadataParser:
    def __init__(self, config: CGConfig) -> None:
        self.status_db: Store = config.status_db
        self.lims: LimsAPI = config.lims_api

    def parse_metadata(self, case_internal_id: str) -> SamplesMetadata:
        metadata_for_case = self.parse_metadata_for_case(case_internal_id)
        metadata_for_internal_negative_control = self.parse_metadata_for_internal_negative_control(metadata_for_case)

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
                target_reads=sample.application_version.application.target_reads,
                percent_reads_guaranteed=sample.application_version.application.percent_reads_guaranteed,
            )

            metadata_for_case[sample.internal_id] = sample_metadata

        return metadata_for_case

    def parse_metadata_for_internal_negative_control(self, metadata_for_case: SamplesMetadata) -> dict[str, SampleMetadata]:
        sample_internal_id = metadata_for_case.keys()[0] 

        internal_negative_control_id = get_internal_negative_control_id_from_lims(self, sample_internal_id)

        #return dict[internal_negative_control_id, get_internal_negative_control_metadata]

        pass

def get_negative_controls_from_list(samples: list[Sample]) -> list[Sample]:
        """Filter and return a list of internal negative controls from a given sample list."""
        negative_controls = []
        for sample in samples:
            if sample.udf.get("Control") == "negative" and sample.udf.get("customer") == "cust000":
                negative_controls.append(sample)
        return negative_controls

    def get_internal_negative_control_id_from_lims(self, sample_internal_id) -> str:

    # LimsAPI
        artifact = self.lims.get_latest_artifact_for_sample(LimsProcess.COVID_POOLING_STEP, LimsArtifactTypes.ANALYTE, sample_internal_id)
        if not artifact:
            return None
        negative_controls = get_negative_controls_from_list(samples=artifact[0].samples)
        if not negative_controls:
            return None
        return negative_controls[0].id


    