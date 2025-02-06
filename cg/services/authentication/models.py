from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    id: int
    username: str
    email: str
    role: str
