from typing import Annotated

from pydantic import BeforeValidator, Field

from cg.constants import SexOptions
from cg.models.qc_metrics import QCMetrics


def convert_sex(plink_sex: float) -> SexOptions:
    if plink_sex == 2:
        return SexOptions.FEMALE
    elif plink_sex == 1:
        return SexOptions.MALE
    elif plink_sex == 0:
        return SexOptions.UNKNOWN
    else:
        raise NotImplementedError


class NalloQCMetrics(QCMetrics):
    """Nallo QC metrics."""

    avg_sequence_length: float | None
    coverage_bases: float | None
    median_coverage: float | None
    percent_duplicates: float | None
    predicted_sex: Annotated[SexOptions, BeforeValidator(convert_sex)] = Field(alias="somalier_sex")
