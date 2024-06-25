"""FOHM report models."""

from pydantic import BaseModel, Field


class FohmComplementaryReport(BaseModel):
    """Model for validating FOHM complementary reports."""

    sample_number: str = Field(str, alias="provnummer")
    selection_criteria: str = Field(str, alias="urvalskriterium")
    gsaid_accession: str = Field(str, alias="GISAID_accession")


class FohmPangolinReport(BaseModel):
    """Model for validating FOHM Pangolin reports."""

    taxon: str
    lineage: str
    conflict: str
    ambiguity_score: str
    scorpio_call: str
    scorpio_support: str
    scorpio_conflict: str
    scorpio_notes: str
    version: str
    pangolin_version: str
    scorpio_version: str
    constellation_version: str
    is_designated: str
    qc_status: str
    qc_notes: str
    note: str
