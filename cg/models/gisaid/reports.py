"""GISAID report models."""

from pydantic import BaseModel, Field


class GisaidComplementaryReport(BaseModel):
    """Model for validating a GSAID complementary reports."""

    gsaid_accession: str = None
    sample_number: str = Field(str, alias="provnummer")
    selection_criteria: str = Field(str, alias="urvalskriterium")
