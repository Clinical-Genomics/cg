from typing import Optional

from pydantic import BaseModel

from cg.constants.subject import Gender


class Subject(BaseModel):
    subject_id: str
    sample_ids: set[str]
    gender: Optional[Gender] = Gender.MISSING
