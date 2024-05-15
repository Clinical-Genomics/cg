from cg.constants.constants import ControlOptions
from cg.meta.workflow.mutant.metadata_parser.models import SampleMetadata
from cg.store.models import Sample
from cg.apps.lims.api import LimsAPI
from cg.constants.lims import LimsArtifactTypes, LimsProcess


def is_sample_external_negative_control(sample: Sample) -> bool:
    return sample.control == ControlOptions.NEGATIVE


# TODO: Do we ever run the risk of having several controls in one covid pool artifact?
# def get_negative_controls_from_list(samples: list[Sample]) -> list[Sample]:
#     """Filter and return a list of internal negative controls from a given sample list."""
#     negative_controls = []
#     for sample in samples:
#         if sample.udf.get("Control") == "negative" and sample.udf.get("customer") == "cust000":
#             negative_controls.append(sample)
#     return negative_controls


def get_internal_negative_control_id_from_lims(lims: LimsAPI, sample_internal_id: str) -> str:
    artifact = lims.get_latest_artifact_for_sample(
        LimsProcess.COVID_POOLING_STEP, LimsArtifactTypes.ANALYTE, sample_internal_id
    )
    if not artifact:
        return None

    samples = artifact[0].samples

    for sample in samples:
        if sample.udf.get("Control") == "negative" and sample.udf.get("customer") == "cust000":
            internal_negative_control = sample
            return internal_negative_control.id


def get_internal_negative_control_id(lims: LimsAPI, metadata_for_case: SampleMetadata) -> str:
    """Query lims to retrive internal_negative_control_id."""
    sample_internal_id = metadata_for_case.keys()[0]  # internal_id of sample from covid pool

    internal_negative_control_id = get_internal_negative_control_id_from_lims(
        lims, sample_internal_id
    )

    return internal_negative_control_id
