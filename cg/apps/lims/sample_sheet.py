"""Functions to get sample sheet information from Lims."""

import logging
import re
from typing import Iterable, Type

from genologics.entities import Artifact, Container, Sample
from genologics.lims import Lims

from cg.apps.demultiplex.sample_sheet.sample_models import IlluminaSampleIndexSetting

LOG = logging.getLogger(__name__)


def get_placement_lane(lane: str) -> int:
    """Parse out the lane information from an artifact.placement."""
    return int(lane.split(":")[0])


def get_non_pooled_artifacts(artifact: Artifact) -> list[Artifact]:
    """Find the parent artifact of the sample. Should hold the reagent_label."""
    artifacts = []

    if len(artifact.samples) == 1:
        artifacts.append(artifact)
        return artifacts

    for artifact_input in artifact.input_artifact_list():
        artifacts.extend(get_non_pooled_artifacts(artifact_input))

    return artifacts


def get_reagent_label(artifact) -> str | None:
    """Get the first and only reagent label from an artifact."""
    labels: list[str] = artifact.reagent_labels
    if len(labels) > 1:
        raise ValueError(f"Expecting at most one reagent label. Got ({len(labels)}).")
    return labels[0] if labels else None


def extract_sequence_in_parentheses(label: str) -> str | None:
    """Return the sequence in parentheses from the reagent label or None if not found."""
    match = re.match(r"^[^(]+ \(([^)]+)\)$", label)
    return match.group(1) if match else None


def get_index(lims: Lims, label: str) -> str:
    """Parse out the sequence from a reagent label."""

    reagent_types = lims.get_reagent_types(name=label)

    if len(reagent_types) > 1:
        raise ValueError(f"Expecting at most one reagent type. Got ({len(reagent_types)}).")

    try:
        reagent_type = reagent_types.pop()
    except IndexError:
        return ""
    sequence: str = reagent_type.sequence

    match = extract_sequence_in_parentheses(label=label)
    if match:
        assert match == sequence

    return sequence


def get_flow_cell_samples(
    lims: Lims,
    flow_cell_id: str,
) -> Iterable[IlluminaSampleIndexSetting]:
    """Return samples from LIMS for a given flow cell."""
    LOG.info(f"Fetching samples from lims for flowcell {flow_cell_id}")
    containers: list[Container] = lims.get_containers(name=flow_cell_id)
    if not containers:
        return []
    container: Container = containers[-1]  # only take the last one. See ÖA#217.
    raw_lanes: list[str] = sorted(container.placements.keys())
    for raw_lane in raw_lanes:
        lane: int = get_placement_lane(raw_lane)
        placement_artifact: Artifact = container.placements[raw_lane]
        non_pooled_artifacts: list[Artifact] = get_non_pooled_artifacts(placement_artifact)
        for artifact in non_pooled_artifacts:
            sample: Sample = artifact.samples[0]  # we are assured it only has one sample
            label: str | None = get_reagent_label(artifact)
            index = get_index(lims=lims, label=label)
            yield IlluminaSampleIndexSetting(
                lane=lane,
                sample_id=sample.id,
                index=index,
            )
