from pydantic import BaseModel


class OrderOpenPatch(BaseModel):
    open: bool
