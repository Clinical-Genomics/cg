from typing import Annotated

from pydantic import BeforeValidator, Field

from cg.constants import SexOptions
from cg.models.qc_metrics import QCMetrics, convert_sex


class NalloQCMetrics(QCMetrics):
    """Nallo QC metrics."""

    avg_sequence_length: float | None
    coverage_bases: float | None
    median_coverage: float | None
    percent_duplicates: float | None
    predicted_sex: Annotated[SexOptions, BeforeValidator(convert_sex)] = Field(alias="somalier_sex")
