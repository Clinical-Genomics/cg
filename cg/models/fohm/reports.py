"""FOHM report models."""

from pydantic import BaseModel, Field


class FohmReport(BaseModel):
    """Model for validating FOHM reports."""

    sample_number: str = Field(str, alias="provnummer")
    selection_criteria: str = Field(str, alias="urvalskriterium")
    gsaid_accession: str = Field(str, alias="GISAID_accession")
