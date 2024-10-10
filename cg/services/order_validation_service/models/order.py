from pydantic import BaseModel, Field, model_validator

from cg.constants import DataDelivery
from cg.constants.constants import Workflow

TICKET_PATTERN = r"^#\d{4,}"


class Order(BaseModel):
    comment: str | None = None
    connect_to_ticket: bool = False
    customer: str = Field(min_length=1)
    delivery_type: DataDelivery
    name: str = Field(min_length=1)
    skip_reception_control: bool = False
    ticket_number: str | None = Field(None, pattern=TICKET_PATTERN)
    user_id: int
    workflow: Workflow

    @model_validator(mode="before")
    def convert_empty_strings_to_none(cls, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if value == "":
                    data[key] = None
        return data
