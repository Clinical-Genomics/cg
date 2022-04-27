from typing import Optional, List

from pydantic import BaseModel

from cg.constants.subject import Gender


class Biopsi(BaseModel):
    sample_ids: set[str]
    tissue: Optional[str]


class Subject(BaseModel):
    organism_id: str
    subject_id: str
    sample_ids: set[str]


class SubjectHuman(Subject):
    biopsis: Optional[List[Biopsi]]
    gender: Optional[Gender] = Gender.MISSING
