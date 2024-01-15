"""This module holds the definition of the field present in the pipeline qc metrics yaml file."""
from pydantic import BaseModel


class PipelineQCMetricsFields(BaseModel):
    """Definition for elements in deliverables metrics file."""

    header: str  # sample or case
    id: str  # sample id
    category: str  # Sequencing, Coverage, pipeline specific
    level: str  # concatenated, lane or None
    input: str
    name: str
    step: str
    value: any
