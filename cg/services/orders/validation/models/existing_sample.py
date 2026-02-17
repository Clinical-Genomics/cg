from pydantic import BaseModel, Field, field_validator

from cg.models.orders.sample_base import NAME_PATTERN, StatusEnum


class ExistingSample(BaseModel):
    father: str | None = Field(None, pattern=NAME_PATTERN)
    internal_id: str
    mother: str | None = Field(None, pattern=NAME_PATTERN)
    status: StatusEnum | None = None

    @property
    def is_new(self) -> bool:
        return False


class ExistingRNAFusionSample(ExistingSample):
    """Model with special tumour validation for existing RNAFUSION samples."""

    tumour: bool = True

    @field_validator("tumour", mode="before")
    @classmethod
    def default_and_validate_tumour(cls, v) -> bool:
        """Ensure that the tumour field is always set to True.
        If it is not provided, it defaults to True.
        If it is provided and not True, raise a ValueError.
        """
        if v is None:
            return True
        if v is not True:
            raise ValueError("Can't perform RNAFUSION analysis on non-tumour samples")
        return v
