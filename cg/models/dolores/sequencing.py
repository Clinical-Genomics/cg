from pydantic import BaseModel


class Sequencing(BaseModel):
    application_id: str
    sequence_reads: int
