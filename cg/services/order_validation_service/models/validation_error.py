from pydantic import BaseModel


class ValidationError(BaseModel):
    field: str
    message: str


class ValidationErrors(BaseModel):
    errors: list[ValidationError]
