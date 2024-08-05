from pydantic import BaseModel


class OrderDeliveredPatch(BaseModel):
    delivered: bool
