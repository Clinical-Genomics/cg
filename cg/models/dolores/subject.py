from typing import Optional, List, Set

from pydantic import BaseModel

from cg.constants.subject import Gender


class Biopsi(BaseModel):
    sample_ids: Set[str]
    tissue: Optional[str]


class Subject(BaseModel):
    organism_id: str
    subject_id: str
    sample_ids: Set[str]


class SubjectHuman(Subject):
    biopsies: Optional[List[Biopsi]]
    gender: Optional[Gender] = Gender.MISSING
