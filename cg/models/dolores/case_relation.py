import datetime
from typing import Optional, List

from pydantic import BaseModel

from cg.constants.subject import PhenotypeStatus, Gender


class CaseSample(BaseModel):
    sample_id: str
    father: Optional[str]
    mother: Optional[str]
    phenotype_status: Optional[PhenotypeStatus]
    gender: Optional[Gender] = Gender.MISSING


class CaseRelation(BaseModel):
    case_id: str
    created_at: datetime.date = None
    samples: List[CaseSample]
    updated_at: datetime.date = None
