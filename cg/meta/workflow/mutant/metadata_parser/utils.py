from cg.constants.constants import ControlOptions
from cg.exc import LimsDataError
from cg.store.models import Case, Sample
from cg.apps.lims.api import LimsAPI
from cg.constants.lims import LimsArtifactTypes, LimsProcess
from genologics.entities import Artifact
from genologics.entities import Sample as LimsSample
from cg.models.cg_config import LOG


def is_sample_external_negative_control(sample: Sample) -> bool:
    return sample.control == ControlOptions.NEGATIVE


def get_negative_controls_from_list(samples: list[LimsSample]) -> list[LimsSample]:
    """Filter and return a list of internal negative controls from a given sample list."""
    negative_controls = []
    for sample in samples:
        if sample.udf.get("Control") == "negative" and sample.udf.get("customer") == "cust000":
            negative_controls.append(sample)
    return negative_controls


def get_internal_negative_control_id_from_lims(lims: LimsAPI, sample_internal_id: str) -> str:
    """Retrieve from lims the sample_id for the internal negative control sample present in the same pool as the given sample."""
    try:
        artifact: Artifact = lims.get_latest_artifact_for_sample(
            LimsProcess.COVID_POOLING_STEP, LimsArtifactTypes.ANALYTE, sample_internal_id
        )
        samples = artifact[0].samples

        negative_controls: list = get_negative_controls_from_list(samples=samples)

        if len(negative_controls) > 1:
            sample_ids = [sample.id for sample in negative_controls]
            LOG.warning(f"Several internal negative control samples found: {' '.join(sample_ids)}")
        else:
            return negative_controls[0].id
    except Exception as exception_object:
        raise LimsDataError from exception_object


def get_internal_negative_control_id(lims: LimsAPI, case: Case) -> str:
    """Query lims to retrive internal_negative_control_id."""

    sample_internal_id = case.sample_ids[0]

    internal_negative_control_id: str = get_internal_negative_control_id_from_lims(
        lims=lims, sample_internal_id=sample_internal_id
    )

    return internal_negative_control_id
