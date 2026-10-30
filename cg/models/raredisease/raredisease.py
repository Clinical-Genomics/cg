from typing import Annotated

from pydantic import BeforeValidator, Field

from cg.constants.constants import SexOptions
from cg.models.qc_metrics import QCMetrics, convert_sex


class RarediseaseQCMetrics(QCMetrics):
    """Raredisease QC metrics."""

    percent_duplication: float
    picard_pct_pf_reads_aligned: float
    predicted_sex: Annotated[SexOptions, BeforeValidator(convert_sex)] = Field(alias="somalier_sex")
