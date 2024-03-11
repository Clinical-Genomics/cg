from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated


def parse_case_ids(input: list[str]) -> list[str]:
    return input[0].split(",") if input else []


class DeliveryMessageRequest(BaseModel):
    case_ids: Annotated[list[str], BeforeValidator(parse_case_ids)]
