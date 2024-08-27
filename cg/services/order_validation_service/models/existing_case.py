from pydantic import BaseModel


class ExistingCase(BaseModel):
    internal_id: str
    panels: list[str]

    @property
    def is_new(self) -> bool:
        return False
