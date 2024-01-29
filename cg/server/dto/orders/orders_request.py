from pydantic import BaseModel


class OrdersRequest(BaseModel):
    limit: int | None = None
