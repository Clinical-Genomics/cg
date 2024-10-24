from pydantic import BaseModel


class DeliveryFileTags(BaseModel):
    case_tags: list[set[str]] | None
    sample_tags: list[set[str]]
