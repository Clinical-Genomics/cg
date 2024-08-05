from pydantic import BaseModel


class DeliveryMessageResponse(BaseModel):
    message: str


class DeliveryMessageOrderResponse(DeliveryMessageResponse):
    analysis_ids: list[int]
