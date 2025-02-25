from pydantic import BaseModel


class ApplicationResponse(BaseModel):
    applications: list[str]
