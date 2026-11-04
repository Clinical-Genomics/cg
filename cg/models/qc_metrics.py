from pydantic import BaseModel

from cg.constants import SexOptions


def convert_sex(plink_sex: float) -> SexOptions:
    if plink_sex == 2:
        return SexOptions.FEMALE
    elif plink_sex == 1:
        return SexOptions.MALE
    elif plink_sex == 0:
        return SexOptions.UNKNOWN
    else:
        raise NotImplementedError


class QCMetrics(BaseModel):
    """QC metrics analysis model."""
