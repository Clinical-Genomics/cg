"""Data classes relevant to the sequencing runs."""

from pydantic import BaseModel


class RunData(BaseModel):
    """Holds information for a sequencing run."""

    pass


class RunMetrics(BaseModel):
    """Holds the metrics for a sequencing run."""

    pass


class PostProcessingDTOs(BaseModel):
    """Data transfer objects for the post-processing service."""

    pass
