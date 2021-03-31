"""Functions to get sample sheet information from Lims"""
import logging
import re
from typing import Iterable, List, Optional

from genologics.entities import Artifact, Container, Sample
from genologics.lims import Lims
from pydantic import BaseModel

LOG = logging.getLogger(__name__)


class LimsFlowcellSample(BaseModel):
    flowcell_id: str
    lane: int
    sample_id: str
    sample_ref: str = "hg19"
    index: str
    index2: str = ""
    description: str = ""
    sample_name: str
    control: str = "N"
    recipe: str = "R1"
    operator: str = "script"
    project: str


def get_placement_lane(lane: str) -> int:
    """Parse out the lane information from an artifact.placement"""
    return int(lane.split(":")[0])


def get_non_pooled_artifacts(artifact: Artifact) -> List[Artifact]:
    """Find the parent artifact of the sample. Should hold the reagent_label"""
    artifacts = []

    if len(artifact.samples) == 1:
        artifacts.append(artifact)
        return artifacts

    for artifact_input in artifact.input_artifact_list():
        artifacts.extend(get_non_pooled_artifacts(artifact_input))

    return artifacts


def get_reagent_label(artifact) -> Optional[str]:
    """Get the first and only reagent label from an artifact"""
    labels: List[str] = artifact.reagent_labels
    if len(labels) > 1:
        raise ValueError("Expecting at most one reagent label. Got ({}).".format(len(labels)))
    return labels[0] if labels else None


def get_index(lims: Lims, label: str) -> str:
    """Parse out the sequence from a reagent label"""

    reagent_types = lims.get_reagent_types(name=label)

    if len(reagent_types) > 1:
        raise ValueError("Expecting at most one reagent type. Got ({}).".format(len(reagent_types)))

    try:
        reagent_type = reagent_types.pop()
    except IndexError:
        return ""
    sequence = reagent_type.sequence

    match = re.match(r"^.+ \((.+)\)$", label)
    if match:
        assert match.group(1) == sequence

    return sequence


def flowcell_samples(lims: Lims, flowcell_id: str) -> Iterable[LimsFlowcellSample]:
    LOG.info("Fetching samples from lims for flowcell %s", flowcell_id)
    containers: List[Container] = lims.get_containers(name=flowcell_id)
    if not containers:
        return []
    container: Container = containers[-1]  # only take the last one. See ÖA#217.
    raw_lanes: List[str] = sorted(container.placements.keys())
    for raw_lane in raw_lanes:
        lane: int = get_placement_lane(raw_lane)
        placement_artifact: Artifact = container.placements[raw_lane]
        non_pooled_artifacts: List[Artifact] = get_non_pooled_artifacts(placement_artifact)
        for artifact in non_pooled_artifacts:
            sample: Sample = artifact.samples[0]  # we are assured it only has one sample
            label: Optional[str] = get_reagent_label(artifact)
            index = get_index(lims=lims, label=label)
            yield LimsFlowcellSample(
                flowcell_id=flowcell_id,
                lane=lane,
                sample_id=sample.id,
                index=index,
                sample_name=sample.name,
                project=sample.project.name,
            )
