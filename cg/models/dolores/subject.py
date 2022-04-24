from typing import Optional

from pydantic import BaseModel

from cg.constants.subject import Gender


class Subject(BaseModel):
    gender: Optional[Gender] = Gender.MISSING
    organism_id: str
    subject_id: str
    sample_ids: set[str]
