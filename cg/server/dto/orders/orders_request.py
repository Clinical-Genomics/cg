from pydantic import BaseModel


class OrdersRequest(BaseModel):
    limit: int | None = None
    workflow: str | None = None
