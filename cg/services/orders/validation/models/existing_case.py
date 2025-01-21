from pydantic import BaseModel


class ExistingCase(BaseModel):
    internal_id: str
    panels: list[str] | None = None

    @property
    def is_new(self) -> bool:
        return False
