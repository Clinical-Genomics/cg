from pydantic import BaseModel, BeforeValidator, Field, PrivateAttr, model_validator
from typing_extensions import Annotated

from cg.constants import DataDelivery
from cg.models.orders.constants import OrderType
from cg.services.orders.validation.models.utils import set_null_to_false


class Order(BaseModel):
    comment: str | None = None
    customer: str = Field(min_length=1)
    delivery_type: DataDelivery
    order_type: OrderType = Field(alias="project_type")
    name: str = Field(min_length=1, max_length=64)
    skip_reception_control: Annotated[bool, BeforeValidator(set_null_to_false)] = False
    _generated_ticket_id: int | None = PrivateAttr(default=None)
    _user_id: int = PrivateAttr(default=None)

    @model_validator(mode="before")
    def convert_empty_strings_to_none(cls, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if value == "":
                    data[key] = None
        return data
