from pydantic import BaseModel


class DeliveryMessageResponse(BaseModel):
    message: str
