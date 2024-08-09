from pydantic import BaseModel


class CollaboratorSamplesRequest(BaseModel):
    enquiry: str
    customer: str
    limit: int = 50
