"""Chanjo2 API pydantic models."""

from pydantic import BaseModel, RootModel, field_validator


class CoverageSample(BaseModel):
    """Chanjo2 sample model defined with an ID and a coverage file path."""

    coverage_file_path: str
    name: str


class CoveragePostRequest(BaseModel):
    """Chanjo2 coverage POST request model."""

    build: str
    coverage_threshold: int
    hgnc_gene_ids: list[int]
    interval_type: str
    samples: list[CoverageSample]


class CoverageMetrics(BaseModel):
    """Chanjo2 sample coverage metrics."""

    coverage_completeness_percent: float
    mean_coverage: float


class CoveragePostResponse(RootModel):
    """Coverage sample data model returned from the POST request."""

    root: dict[str, CoverageMetrics]

    @field_validator("root")
    @classmethod
    def root_must_not_be_empty(cls, root: dict[str, CoverageMetrics]):
        if not root:
            raise ValueError("Coverage POST response must not be an empty dictionary")
        return root

    def get_sample_coverage_metrics(self, sample_id: str) -> CoverageMetrics:
        """Return the coverage metrics for the specified sample ID."""
        if sample_id not in self.root:
            raise ValueError(f"Sample ID '{sample_id}' not found in the coverage POST response")
        return self.root[sample_id]
