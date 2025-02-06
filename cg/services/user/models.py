from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    """
    Data model for an authenticated user. Contains information required in the Flask API.
    attributes:
        id: int Databse id of the user
        name: str 
        email: str 
        role: str Role of the user
    """
    id: int
    name: str
    email: str
    role: str
