"""Chanjo2 API pydantic models."""

from pydantic import BaseModel


class CoverageSample(BaseModel):
    """Chanjo2 sample model defined with an ID and a coverage file path."""

    coverage_file_path: str
    name: str


class CoverageRequest(BaseModel):
    """Chanjo2 coverage POST request model."""

    build: str
    coverage_threshold: int
    hgnc_gene_ids: list[int]
    interval_type: str
    samples: list[CoverageSample]


class CoverageData(BaseModel):
    """Coverage data model returned from the POST request."""

    coverage_completeness_percent: float
    mean_coverage: float
