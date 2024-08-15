from pydantic import BaseModel


class OrderOpenPatch(BaseModel):
    is_open: bool
