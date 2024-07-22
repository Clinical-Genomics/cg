"""Chanjo2 API pydantic models."""

from pydantic import BaseModel


class Chanjo2Sample(BaseModel):
    """Chanjo2 sample model defined with an ID and a coverage file path."""

    coverage_path: str
    id: str


class CoverageRequest(BaseModel):
    """Chanjo2 coverage POST request model."""

    build: str
    coverage_threshold: int
    gene_ids: list[int]
    interval_type: str
    samples: list[Chanjo2Sample]


class CoverageData(BaseModel):
    """Coverage data model returned from the POST request."""

    mean_coverage: float
    coverage_completeness_percent: float
