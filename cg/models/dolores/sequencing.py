from pydantic import BaseModel


class Sequencing(BaseModel):
    application_id: str
    reads: int
