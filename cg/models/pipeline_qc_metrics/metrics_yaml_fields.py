"""This module holds the definition of the field present in the pipeline qc metrics yaml file."""
from pydantic import BaseModel


class PipelineQCMetricsFields(BaseModel):
    """Definition for elements in deliverables metrics file."""

    header: str  # describes the level of the metric sample or case
    id: str  # sample id

    category: str  # Sequencing, Coverage, pipeline specific
    category_level: str  # concatenated, lane or None

    input: str  # file the info came from
    name: str  # name of the metric
    step: str  # pipeline step
    value: any  # the value of the metric
